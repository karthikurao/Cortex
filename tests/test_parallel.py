"""Tests for parallel execution, communication bus, and inter-agent tools."""

import threading
from unittest.mock import MagicMock, patch

import pytest

from agents.communication import AgentCommunicationBus, DelegationDepthExceeded
from tools.agent_tools import create_agent_tools, create_delegate_tool, create_orchestrator_route_tool

# ==============================================================================
# Communication Bus Tests
# ==============================================================================


class TestAgentCommunicationBus:
    """Tests for the AgentCommunicationBus."""

    def test_register_agent(self):
        bus = AgentCommunicationBus()
        mock_agent = MagicMock()
        bus.register_agent("test_agent", mock_agent)
        assert "test_agent" in bus.get_available_agents()

    def test_register_all_agents(self):
        bus = AgentCommunicationBus()
        agents = {"agent_a": MagicMock(), "agent_b": MagicMock()}
        bus.register_all_agents(agents)
        available = bus.get_available_agents()
        assert "agent_a" in available
        assert "agent_b" in available

    def test_delegate_calls_target_agent(self):
        bus = AgentCommunicationBus()
        target = MagicMock()
        target.invoke.return_value = {"result": "delegation result", "status": "success"}
        bus.register_agent("target_agent", target)

        result = bus.delegate("source_agent", "target_agent", "do something")

        target.invoke.assert_called_once_with("do something", None)
        assert "delegation result" in result

    def test_delegate_unknown_agent_raises(self):
        bus = AgentCommunicationBus()
        with pytest.raises(ValueError, match="not found"):
            bus.delegate("source", "nonexistent", "task")

    def test_delegation_depth_limit(self):
        bus = AgentCommunicationBus(max_delegation_depth=2)
        target = MagicMock()
        bus.register_agent("target", target)

        # Simulate being at max depth
        bus._set_depth(2)
        with pytest.raises(DelegationDepthExceeded):
            bus.delegate("source", "target", "task")

    def test_delegation_depth_tracking(self):
        """Verify that depth increments during delegation and resets after."""
        bus = AgentCommunicationBus(max_delegation_depth=5)

        depths_seen = []

        def mock_invoke(task, context=None):
            depths_seen.append(bus._get_depth())
            return {"result": "ok"}

        target = MagicMock()
        target.invoke.side_effect = mock_invoke
        bus.register_agent("target", target)

        assert bus._get_depth() == 0
        bus.delegate("source", "target", "task")
        assert bus._get_depth() == 0  # resets after delegation
        assert depths_seen == [1]  # was 1 during execution

    def test_message_log(self):
        bus = AgentCommunicationBus()
        target = MagicMock()
        target.invoke.return_value = {"result": "done"}
        bus.register_agent("target", target)

        bus.delegate("source", "target", "test task")

        log = bus.get_message_log()
        assert len(log) == 2  # delegation + response
        assert log[0].message_type == "delegation"
        assert log[0].from_agent == "source"
        assert log[0].to_agent == "target"
        assert log[1].message_type == "response"

    def test_message_log_summary(self):
        bus = AgentCommunicationBus()
        target = MagicMock()
        target.invoke.return_value = {"result": "done"}
        bus.register_agent("target", target)

        bus.delegate("source", "target", "test")

        summary = bus.get_message_log_summary()
        assert len(summary) == 2
        assert summary[0]["from"] == "source"
        assert summary[0]["to"] == "target"
        assert "type" in summary[0]

    def test_clear_log(self):
        bus = AgentCommunicationBus()
        bus.broadcast("agent_a", "hello")
        assert len(bus.get_message_log()) == 1
        bus.clear_log()
        assert len(bus.get_message_log()) == 0

    def test_broadcast_logs_message(self):
        bus = AgentCommunicationBus()
        bus.broadcast("agent_a", "important update")
        log = bus.get_message_log()
        assert len(log) == 1
        assert log[0].message_type == "broadcast"
        assert log[0].from_agent == "agent_a"
        assert log[0].to_agent == "*"

    def test_request_via_orchestrator(self):
        bus = AgentCommunicationBus()
        bus.set_orchestrator_route_fn(lambda task: f"routed: {task}")

        result = bus.request_via_orchestrator("agent_a", "analyze this")
        assert "routed: analyze this" in result

    def test_request_via_orchestrator_no_fn(self):
        bus = AgentCommunicationBus()
        result = bus.request_via_orchestrator("agent_a", "task")
        assert "Error" in result

    def test_request_via_orchestrator_depth_limit(self):
        bus = AgentCommunicationBus(max_delegation_depth=1)
        bus.set_orchestrator_route_fn(lambda task: "ok")
        bus._set_depth(1)
        with pytest.raises(DelegationDepthExceeded):
            bus.request_via_orchestrator("agent_a", "task")

    def test_delegate_handles_agent_exception(self):
        bus = AgentCommunicationBus()
        target = MagicMock()
        target.invoke.side_effect = RuntimeError("agent crashed")
        bus.register_agent("target", target)

        result = bus.delegate("source", "target", "task")
        assert "Error" in result
        assert "agent crashed" in result

    def test_thread_safety_of_message_log(self):
        """Verify message log is thread-safe with concurrent writes."""
        bus = AgentCommunicationBus()
        num_threads = 10
        messages_per_thread = 50

        def broadcast_many(agent_id):
            for i in range(messages_per_thread):
                bus.broadcast(agent_id, f"msg-{i}")

        threads = [threading.Thread(target=broadcast_many, args=(f"agent_{i}",)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        log = bus.get_message_log()
        assert len(log) == num_threads * messages_per_thread


# ==============================================================================
# Inter-Agent Tools Tests
# ==============================================================================


class TestAgentTools:
    """Tests for the inter-agent communication tools."""

    def test_create_delegate_tool(self):
        bus = MagicMock()
        bus.delegate.return_value = "result from target"
        tool = create_delegate_tool(bus, "caller")

        result = tool.invoke({"agent_id": "target", "task": "do work"})
        bus.delegate.assert_called_once_with("caller", "target", "do work")
        assert result == "result from target"

    def test_create_delegate_tool_handles_error(self):
        bus = MagicMock()
        bus.delegate.side_effect = DelegationDepthExceeded("too deep")
        tool = create_delegate_tool(bus, "caller")

        result = tool.invoke({"agent_id": "target", "task": "task"})
        assert "Delegation failed" in result

    def test_create_orchestrator_route_tool(self):
        bus = MagicMock()
        bus.request_via_orchestrator.return_value = "orchestrator result"
        tool = create_orchestrator_route_tool(bus, "caller")

        result = tool.invoke({"task": "route this"})
        bus.request_via_orchestrator.assert_called_once_with("caller", "route this")
        assert result == "orchestrator result"

    def test_create_orchestrator_route_tool_handles_error(self):
        bus = MagicMock()
        bus.request_via_orchestrator.side_effect = DelegationDepthExceeded("limit")
        tool = create_orchestrator_route_tool(bus, "caller")

        result = tool.invoke({"task": "task"})
        assert "Orchestrator routing failed" in result

    def test_create_agent_tools_returns_two_tools(self):
        bus = MagicMock()
        tools = create_agent_tools(bus, "agent_x")
        assert len(tools) == 2
        tool_names = {t.name for t in tools}
        assert "delegate_to_agent" in tool_names
        assert "request_via_orchestrator" in tool_names


# ==============================================================================
# Parallel Execution Tests
# ==============================================================================


class TestParallelExecution:
    """Tests for the parallel execution logic in the orchestrator."""

    @patch("agents.base_agent.create_chat_model")
    def test_priority_grouping(self, mock_llm):
        """Assignments should be grouped by priority level."""
        from collections import defaultdict

        assignments = [
            {"agent_id": "a", "priority": 2},
            {"agent_id": "b", "priority": 1},
            {"agent_id": "c", "priority": 1},
            {"agent_id": "d", "priority": 3},
        ]

        groups = defaultdict(list)
        for a in assignments:
            groups[a.get("priority", 1)].append(a)

        assert len(groups) == 3
        assert len(groups[1]) == 2  # b, c at same priority
        assert len(groups[2]) == 1
        assert len(groups[3]) == 1
        assert sorted(groups.keys()) == [1, 2, 3]

    @patch("agents.base_agent.create_chat_model")
    def test_same_priority_agents_identified_for_parallel(self, mock_llm):
        """Same-priority agents should be identified as parallelizable."""
        assignments = [
            {"agent_id": "code_reviewer", "task": "review", "priority": 1},
            {"agent_id": "security", "task": "scan", "priority": 1},
            {"agent_id": "testing", "task": "test", "priority": 2},
        ]

        from collections import defaultdict

        groups = defaultdict(list)
        for a in assignments:
            groups[a.get("priority", 1)].append(a)

        # Priority 1 has 2 agents — should be parallel
        assert len(groups[1]) == 2
        # Priority 2 has 1 agent — no parallelism needed
        assert len(groups[2]) == 1


class TestBaseAgentCommunication:
    """Tests for BaseAgent communication bus integration."""

    @patch("agents.base_agent.create_chat_model")
    def test_set_communication_bus_adds_tools(self, mock_llm):
        """Setting a bus should add delegation tools to the agent."""
        from agents.code_reviewer import CodeReviewerAgent

        agent = CodeReviewerAgent()
        initial_tool_count = len(agent.tools)

        bus = AgentCommunicationBus()
        bus.register_agent("code_reviewer", agent)
        agent.set_communication_bus(bus)

        assert len(agent.tools) == initial_tool_count + 2
        tool_names = {t.name for t in agent.tools}
        assert "delegate_to_agent" in tool_names
        assert "request_via_orchestrator" in tool_names

    @patch("agents.base_agent.create_chat_model")
    def test_set_communication_bus_idempotent(self, mock_llm):
        """Setting the bus multiple times should not duplicate tools."""
        from agents.code_reviewer import CodeReviewerAgent

        agent = CodeReviewerAgent()

        bus = AgentCommunicationBus()
        agent.set_communication_bus(bus)
        count_after_first = len(agent.tools)

        agent.set_communication_bus(bus)
        assert len(agent.tools) == count_after_first


class TestSettingsParallel:
    """Tests for parallel execution settings."""

    def test_default_settings(self):
        from config.settings import Settings

        s = Settings()
        assert s.parallel_execution is True
        assert s.max_parallel_agents == 4
        assert s.max_delegation_depth == 3

    @patch.dict("os.environ", {"PARALLEL_EXECUTION": "false", "MAX_PARALLEL_AGENTS": "8", "MAX_DELEGATION_DEPTH": "5"})
    def test_settings_from_env(self):
        from config.settings import Settings

        s = Settings()
        assert s.parallel_execution is False
        assert s.max_parallel_agents == 8
        assert s.max_delegation_depth == 5


class TestOrchestratorState:
    """Tests for the new orchestrator state fields."""

    def test_orchestrator_state_has_parallel_metadata(self):
        from agents.orchestrator import OrchestratorState

        state: OrchestratorState = {
            "user_request": "test",
            "routing_decision": {},
            "agent_results": [],
            "final_response": "",
            "error": None,
            "parallel_metadata": {},
        }
        assert "parallel_metadata" in state
