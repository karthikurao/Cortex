"""Master Orchestrator Agent — routes user requests to specialist agents using LangGraph."""

import json
import logging
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
except ImportError:
    ChatNVIDIA = None

try:
    from langchain_ollama import ChatOllama
except ImportError:
    ChatOllama = None

from agents.api_design import APIDesignAgent
from agents.architecture import ArchitectureAgent
from agents.bug_analyzer import BugAnalyzerAgent
from agents.code_reviewer import CodeReviewerAgent
from agents.communication import AgentCommunicationBus
from agents.database import DatabaseAgent
from agents.dependency_audit import DependencyAuditAgent
from agents.devops import DevOpsAgent
from agents.documentation import DocumentationAgent
from agents.exploit_analyzer import ExploitAnalyzerAgent
from agents.performance import PerformanceAgent
from agents.refactoring import RefactoringAgent
from agents.security import SecurityAgent
from agents.testing import TestingAgent
from config.agent_registry import AgentRegistry
from config.settings import settings
from prompts.orchestrator_prompt import ORCHESTRATOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

ROUTING_RETRY_ATTEMPTS = 2


class OrchestratorState(TypedDict):
    """State that flows through the LangGraph orchestration pipeline."""

    user_request: str
    routing_decision: dict[str, Any]
    agent_results: list[dict[str, Any]]
    final_response: str
    error: str | None
    parallel_metadata: dict[str, Any]


class OrchestratorAgent:
    """Master orchestrator that routes requests to specialist agents.

    Uses LangGraph to build a state machine:
    1. classify_intent → Analyzes user request, retries on parse failure, selects agent(s)
    2. execute_agents → Runs assigned agents in parallel by priority group
    3. aggregate_results → Combines all agent outputs into a structured final response

    Features:
    - **Parallel execution** — agents at the same priority level run concurrently
    - **Inter-agent communication** — agents can delegate to each other via AgentCommunicationBus
    - Two delegation modes: direct (agent-to-agent) and master-mediated (through orchestrator)
    - Robust JSON extraction from LLM responses (handles markdown fences, preamble text)
    - Retry on routing parse failure with a stricter follow-up prompt
    - Per-agent error isolation — one agent failure doesn't block others
    - Execution timing and metadata tracking
    - Routing validation against the agent registry
    """

    VALID_AGENT_IDS = {
        "code_reviewer",
        "bug_analyzer",
        "architecture",
        "testing",
        "security",
        "documentation",
        "refactoring",
        "devops",
        "performance",
        "exploit_analyzer",
        "database",
        "api_design",
        "dependency_audit",
    }

    def __init__(self) -> None:
        self.registry = AgentRegistry()
        self._llm = self._create_llm()
        self._agents = self._initialize_agents()
        self._communication_bus = self._initialize_communication_bus()
        self._graph = self._build_graph()

    def _create_llm(self) -> Any:
        """Create the configured LLM client for orchestrator routing."""
        if settings.llm_provider == "nvidia":
            if ChatNVIDIA is None:
                raise ImportError(
                    "langchain-nvidia-ai-endpoints is required for LLM_PROVIDER=nvidia. "
                    "Install it with: pip install langchain-nvidia-ai-endpoints"
                )
            return ChatNVIDIA(**settings.get_llm_kwargs())
        if settings.llm_provider == "ollama":
            if ChatOllama is None:
                raise ImportError(
                    "langchain-ollama is required for LLM_PROVIDER=ollama. "
                    "Install it with: pip install langchain-ollama"
                )
            return ChatOllama(**settings.get_llm_kwargs())
        return ChatOpenAI(**settings.get_llm_kwargs())

    def _initialize_agents(self) -> dict[str, Any]:
        """Create instances of all specialist agents."""
        return {
            "code_reviewer": CodeReviewerAgent(),
            "bug_analyzer": BugAnalyzerAgent(),
            "architecture": ArchitectureAgent(),
            "testing": TestingAgent(),
            "security": SecurityAgent(),
            "documentation": DocumentationAgent(),
            "refactoring": RefactoringAgent(),
            "devops": DevOpsAgent(),
            "performance": PerformanceAgent(),
            "exploit_analyzer": ExploitAnalyzerAgent(),
            "database": DatabaseAgent(),
            "api_design": APIDesignAgent(),
            "dependency_audit": DependencyAuditAgent(),
        }

    def _initialize_communication_bus(self) -> AgentCommunicationBus:
        """Set up the inter-agent communication bus and wire it to all agents."""
        bus = AgentCommunicationBus(max_delegation_depth=settings.max_delegation_depth)
        bus.register_all_agents(self._agents)
        bus.set_orchestrator_route_fn(self._route_for_delegation)

        for agent in self._agents.values():
            agent.set_communication_bus(bus)

        return bus

    def _route_for_delegation(self, task: str) -> str:
        """Internal routing function used for master-mediated inter-agent communication.

        This is called by agents via request_via_orchestrator. It classifies the task
        and executes the selected agent(s), returning the combined result text.
        """
        registry_summary = self.registry.get_registry_summary()
        system_prompt = ORCHESTRATOR_SYSTEM_PROMPT.format(agent_registry=registry_summary)

        try:
            response = self._llm.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=task),
                ]
            )
            routing = self._extract_json(response.content)
            if routing and "assignments" in routing:
                routing = self._validate_routing(routing)
                assignments = routing["assignments"]
                # Execute the first assigned agent (single delegation, not fan-out)
                assignment = assignments[0]
                agent = self._agents.get(assignment["agent_id"])
                if agent:
                    result = agent.invoke(assignment.get("task", task))
                    return result.get("result", str(result)) if isinstance(result, dict) else str(result)
        except Exception as e:
            logger.error("Orchestrator-mediated routing failed: %s", e)

        return f"Could not route delegated task: {task[:200]}"

    def _build_graph(self) -> Any:
        """Build the LangGraph state machine for orchestration."""
        graph = StateGraph(OrchestratorState)

        graph.add_node("classify_intent", self._classify_intent)
        graph.add_node("execute_agents", self._execute_agents)
        graph.add_node("aggregate_results", self._aggregate_results)

        graph.set_entry_point("classify_intent")
        graph.add_edge("classify_intent", "execute_agents")
        graph.add_edge("execute_agents", "aggregate_results")
        graph.add_edge("aggregate_results", END)

        return graph.compile()

    # ------------------------------------------------------------------
    # JSON extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any] | None:
        """Extract JSON from LLM text that may contain markdown fences or preamble."""
        # Try direct parse first
        stripped = text.strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

        # Strip markdown code fences
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", stripped, re.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try to find any JSON object in the text
        brace_match = re.search(r"\{.*\}", stripped, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _validate_routing(self, routing: dict[str, Any]) -> dict[str, Any]:
        """Validate and sanitize the routing decision against the registry."""
        assignments = routing.get("assignments", [])
        valid_assignments = []

        for assignment in assignments:
            agent_id = assignment.get("agent_id", "")
            if agent_id in self.VALID_AGENT_IDS:
                # Ensure required fields
                assignment.setdefault("task", "")
                assignment.setdefault("priority", 1)
                valid_assignments.append(assignment)
            else:
                logger.warning("Ignoring unknown agent_id in routing: %s", agent_id)

        if not valid_assignments:
            # Fallback to code_reviewer if all agents were invalid
            valid_assignments = [
                {
                    "agent_id": "code_reviewer",
                    "task": routing.get("analysis", "Analyze the request"),
                    "priority": 1,
                }
            ]
            routing["analysis"] = (
                routing.get("analysis", "")
                + " (Warning: Original routing had no valid agents — defaulting to code_reviewer)"
            )

        routing["assignments"] = valid_assignments
        return routing

    # ------------------------------------------------------------------
    # Pipeline nodes
    # ------------------------------------------------------------------

    def _classify_intent(self, state: OrchestratorState) -> dict[str, Any]:
        """Analyze the user's request and decide which agents to invoke.

        Includes retry logic: if the first attempt fails to produce valid JSON,
        a stricter follow-up prompt is sent.
        """
        registry_summary = self.registry.get_registry_summary()
        system_prompt = ORCHESTRATOR_SYSTEM_PROMPT.format(agent_registry=registry_summary)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["user_request"]),
        ]

        for attempt in range(1, ROUTING_RETRY_ATTEMPTS + 1):
            try:
                response = self._llm.invoke(messages)
                routing = self._extract_json(response.content)

                if routing and "assignments" in routing:
                    routing = self._validate_routing(routing)
                    return {"routing_decision": routing}

                # If parsing failed, add a correction message for retry
                if attempt < ROUTING_RETRY_ATTEMPTS:
                    messages.append(response)
                    messages.append(
                        HumanMessage(
                            content=(
                                "Your response was not valid JSON or was missing the 'assignments' key. "
                                "Please respond with ONLY a valid JSON object in this exact format:\n"
                                '{"analysis": "...", "assignments": [{"agent_id": "...", "task": "...", "priority": 1}]}'
                            )
                        )
                    )
                    logger.warning("Routing attempt %d failed, retrying with correction prompt", attempt)
            except Exception as e:
                logger.error("Routing attempt %d raised %s: %s", attempt, type(e).__name__, e)
                if attempt >= ROUTING_RETRY_ATTEMPTS:
                    break

        # Ultimate fallback
        logger.warning("All routing attempts failed — using fallback routing to code_reviewer")
        return {
            "routing_decision": {
                "analysis": "Could not determine optimal routing — defaulting to code review.",
                "assignments": [
                    {
                        "agent_id": "code_reviewer",
                        "task": state["user_request"],
                        "priority": 1,
                    }
                ],
            }
        }

    def _execute_agents(self, state: OrchestratorState) -> dict[str, Any]:
        """Execute the assigned agents, using parallel execution for same-priority groups.

        Agents are grouped by priority level. Within each priority group, agents
        execute concurrently using ThreadPoolExecutor. Groups are processed in
        priority order (lower number = higher priority), with a barrier between
        groups so that earlier groups complete before later ones start.

        Results from earlier priority groups are passed as context to later groups.
        """
        # Clear any previous inter-agent messages
        self._communication_bus.clear_log()

        routing = state["routing_decision"]
        assignments = routing.get("assignments", [])

        # Group assignments by priority
        priority_groups: dict[int, list[dict]] = defaultdict(list)
        for assignment in assignments:
            priority = assignment.get("priority", 1)
            priority_groups[priority].append(assignment)

        sorted_priorities = sorted(priority_groups.keys())

        all_results = []
        parallel_meta = {
            "execution_mode": "parallel" if settings.parallel_execution else "sequential",
            "priority_groups": [],
            "total_wall_time_seconds": 0,
            "total_cpu_time_seconds": 0,
        }

        overall_start = time.time()
        prior_results_context = {}

        for priority in sorted_priorities:
            group = priority_groups[priority]
            group_agent_ids = [a.get("agent_id", "?") for a in group]
            group_start = time.time()

            if settings.parallel_execution and len(group) > 1:
                # --- Parallel execution for this priority group ---
                group_results = self._execute_group_parallel(group, state["user_request"], prior_results_context)
            else:
                # --- Sequential execution (single agent or parallel disabled) ---
                group_results = self._execute_group_sequential(group, state["user_request"], prior_results_context)

            group_elapsed = round(time.time() - group_start, 2)
            agent_times = [r.get("metadata", {}).get("execution_time_seconds", 0) for r in group_results]
            sequential_time = sum(agent_times)

            parallel_meta["priority_groups"].append(
                {
                    "priority": priority,
                    "agents": group_agent_ids,
                    "wall_time_seconds": group_elapsed,
                    "sequential_time_seconds": round(sequential_time, 2),
                    "parallel": settings.parallel_execution and len(group) > 1,
                }
            )
            parallel_meta["total_cpu_time_seconds"] += sequential_time

            # Accumulate results and build context for next group
            all_results.extend(group_results)
            for r in group_results:
                if r.get("status") == "success":
                    prior_results_context[r.get("agent_id", "unknown")] = r.get("result", "")[:2000]

        parallel_meta["total_wall_time_seconds"] = round(time.time() - overall_start, 2)

        return {
            "agent_results": all_results,
            "parallel_metadata": parallel_meta,
        }

    def _execute_group_parallel(
        self,
        assignments: list[dict],
        user_request: str,
        prior_context: dict[str, str],
    ) -> list[dict[str, Any]]:
        """Execute a group of agent assignments concurrently using ThreadPoolExecutor."""
        results = []
        max_workers = min(len(assignments), settings.max_parallel_agents)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_assignment = {}
            for assignment in assignments:
                future = executor.submit(self._run_single_agent, assignment, user_request, prior_context)
                future_to_assignment[future] = assignment

            for future in as_completed(future_to_assignment):
                assignment = future_to_assignment[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    agent_id = assignment.get("agent_id", "unknown")
                    logger.error("Parallel agent %s failed: %s", agent_id, e)
                    results.append(
                        {
                            "agent_id": agent_id,
                            "agent_name": "Unknown",
                            "task_description": assignment.get("task", ""),
                            "result": f"Error during parallel execution: {type(e).__name__}: {e}",
                            "status": "error",
                        }
                    )

        return results

    def _execute_group_sequential(
        self,
        assignments: list[dict],
        user_request: str,
        prior_context: dict[str, str],
    ) -> list[dict[str, Any]]:
        """Execute a group of agent assignments sequentially."""
        results = []
        for assignment in assignments:
            result = self._run_single_agent(assignment, user_request, prior_context)
            results.append(result)
        return results

    def _run_single_agent(
        self,
        assignment: dict,
        user_request: str,
        prior_context: dict[str, str],
    ) -> dict[str, Any]:
        """Execute a single agent assignment with error isolation.

        This method is safe to call from multiple threads concurrently.
        Each invocation uses the agent's invoke() which creates its own local state.
        """
        agent_id = assignment.get("agent_id", "")
        task = assignment.get("task", user_request)

        agent = self._agents.get(agent_id)
        if not agent:
            return {
                "agent_id": agent_id,
                "agent_name": "Unknown",
                "task_description": f"Agent '{agent_id}' not found in registry.",
                "result": f"Error: No agent registered with ID '{agent_id}'.",
                "status": "error",
            }

        context = dict(prior_context) if prior_context else None

        try:
            logger.info("Executing agent: %s (task: %s)", agent.name, task[:80])
            agent_start = time.time()
            result = agent.invoke(task, context)
            agent_elapsed = round(time.time() - agent_start, 2)
            result.setdefault("metadata", {})["orchestrator_elapsed_seconds"] = agent_elapsed
            return result
        except Exception as e:
            logger.error("Agent %s failed: %s: %s", agent_id, type(e).__name__, e)
            return {
                "agent_id": agent_id,
                "agent_name": agent.name,
                "task_description": task,
                "result": f"Error during execution: {type(e).__name__}: {e}",
                "status": "error",
            }

    def _aggregate_results(self, state: OrchestratorState) -> dict[str, Any]:
        """Combine results from all agents into a cohesive final response."""
        results = state["agent_results"]
        routing = state["routing_decision"]
        parallel_meta = state.get("parallel_metadata", {})

        parts = []
        parts.append(f"## Orchestrator Analysis\n{routing.get('analysis', 'N/A')}\n")

        success_count = sum(1 for r in results if r.get("status") == "success")
        error_count = sum(1 for r in results if r.get("status") == "error")

        # Execution mode summary
        exec_mode = parallel_meta.get("execution_mode", "sequential")
        wall_time = parallel_meta.get("total_wall_time_seconds", 0)
        cpu_time = parallel_meta.get("total_cpu_time_seconds", 0)
        time_saved = round(cpu_time - wall_time, 2) if cpu_time > wall_time else 0

        parts.append(
            f"**Agents executed:** {len(results)} | ✅ {success_count} succeeded | ❌ {error_count} failed\n"
            f"**Execution mode:** {exec_mode} | ⏱ Wall time: {wall_time}s"
        )
        if time_saved > 0:
            parts.append(f" | ⚡ Saved ~{time_saved}s via parallel execution")
        parts.append("\n")

        # Priority group breakdown
        for group in parallel_meta.get("priority_groups", []):
            mode_label = "⚡ parallel" if group.get("parallel") else "→ sequential"
            parts.append(
                f"  Priority {group['priority']}: [{', '.join(group['agents'])}] "
                f"({mode_label}, {group['wall_time_seconds']}s)\n"
            )

        # Inter-agent communication log
        comm_log = self._communication_bus.get_message_log_summary()
        if comm_log:
            parts.append("\n**🔗 Inter-Agent Communication:**\n")
            for msg in comm_log:
                parts.append(f"  {msg['from']} → {msg['to']} [{msg['type']}]: {msg['content_preview'][:100]}\n")

        for result in results:
            status_icon = "✅" if result["status"] == "success" else "❌"
            metadata = result.get("metadata", {})
            timing = ""
            if "execution_time_seconds" in metadata:
                timing = f" ({metadata['execution_time_seconds']}s)"
            iterations = ""
            if "tool_iterations" in metadata:
                iterations = f" | Tool iterations: {metadata['tool_iterations']}"

            parts.append(
                f"---\n"
                f"## {status_icon} {result['agent_name']} Agent{timing}{iterations}\n\n"
                f"### Task Description\n{result['task_description']}\n\n"
                f"### Result\n{result['result']}\n"
            )

        return {"final_response": "\n".join(parts)}

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def invoke(self, user_request: str) -> dict[str, Any]:
        """Process a user request through the orchestration pipeline.

        Args:
            user_request: The user's natural language request.

        Returns:
            The full orchestration state including routing decisions and agent results.
        """
        initial_state: OrchestratorState = {
            "user_request": user_request,
            "routing_decision": {},
            "agent_results": [],
            "final_response": "",
            "error": None,
            "parallel_metadata": {},
        }
        return self._graph.invoke(initial_state)

    def get_routing_preview(self, user_request: str) -> dict[str, Any]:
        """Preview which agents would be selected without executing them.

        Useful for showing the user the plan before committing to execution.
        """
        registry_summary = self.registry.get_registry_summary()
        system_prompt = ORCHESTRATOR_SYSTEM_PROMPT.format(agent_registry=registry_summary)

        response = self._llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_request),
            ]
        )

        routing = self._extract_json(response.content)
        if routing and "assignments" in routing:
            return self._validate_routing(routing)
        return {"analysis": "Could not parse routing preview", "assignments": []}

    def list_agents(self) -> list[dict[str, str]]:
        """List all available agents with their descriptions."""
        return [
            {
                "id": info.agent_id,
                "name": info.name,
                "description": info.description,
            }
            for info in self.registry.list_all()
        ]
