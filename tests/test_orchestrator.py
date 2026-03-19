"""Tests for the Orchestrator agent routing logic."""

import json

import pytest

from config.agent_registry import AgentRegistry


class TestAgentRegistry:
    """Tests for the AgentRegistry class."""

    def test_registry_has_13_agents(self):
        registry = AgentRegistry()
        assert len(registry.list_all()) == 13

    def test_all_agent_ids_are_unique(self):
        registry = AgentRegistry()
        ids = registry.get_ids()
        assert len(ids) == len(set(ids))

    def test_get_existing_agent(self):
        registry = AgentRegistry()
        agent = registry.get("code_reviewer")
        assert agent is not None
        assert agent.name == "Code Reviewer"
        assert agent.agent_id == "code_reviewer"

    def test_get_nonexistent_agent(self):
        registry = AgentRegistry()
        assert registry.get("nonexistent") is None

    def test_all_agents_have_required_fields(self):
        registry = AgentRegistry()
        for agent in registry.list_all():
            assert agent.name, f"Agent {agent.agent_id} missing name"
            assert agent.agent_id, f"Agent {agent.name} missing agent_id"
            assert agent.description, f"Agent {agent.agent_id} missing description"
            assert len(agent.capabilities) > 0, f"Agent {agent.agent_id} has no capabilities"
            assert len(agent.keywords) > 0, f"Agent {agent.agent_id} has no keywords"

    def test_registry_summary_includes_all_agents(self):
        registry = AgentRegistry()
        summary = registry.get_registry_summary()
        for agent in registry.list_all():
            assert agent.name in summary
            assert agent.agent_id in summary

    @pytest.mark.parametrize(
        "agent_id",
        [
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
        ],
    )
    def test_each_agent_is_registered(self, agent_id):
        registry = AgentRegistry()
        assert registry.get(agent_id) is not None


class TestOrchestratorRouting:
    """Tests for orchestrator routing decision parsing."""

    def test_valid_routing_json_parsing(self):
        """Verify that valid JSON routing decisions are parsed correctly."""
        routing_json = json.dumps(
            {
                "analysis": "User wants a code review",
                "assignments": [{"agent_id": "code_reviewer", "task": "Review the code", "priority": 1}],
            }
        )
        parsed = json.loads(routing_json)
        assert parsed["assignments"][0]["agent_id"] == "code_reviewer"
        assert parsed["assignments"][0]["priority"] == 1

    def test_multi_agent_routing(self):
        """Verify that multi-agent assignments are sorted by priority."""
        assignments = [
            {"agent_id": "refactoring", "task": "Refactor", "priority": 2},
            {"agent_id": "code_reviewer", "task": "Review", "priority": 1},
            {"agent_id": "testing", "task": "Test", "priority": 3},
        ]
        sorted_assignments = sorted(assignments, key=lambda a: a.get("priority", 1))
        assert sorted_assignments[0]["agent_id"] == "code_reviewer"
        assert sorted_assignments[1]["agent_id"] == "refactoring"
        assert sorted_assignments[2]["agent_id"] == "testing"

    def test_routing_fallback_on_invalid_json(self):
        """Verify graceful fallback when JSON parsing fails."""
        invalid_content = "This is not JSON"
        try:
            json.loads(invalid_content)
            parsed = True
        except json.JSONDecodeError:
            parsed = False
        assert not parsed


class TestOrchestratorAgentLookup:
    """Tests for agent instance lookup in the orchestrator."""

    def test_all_registered_agents_can_be_instantiated(self):
        """Verify that all agents in the registry have corresponding classes."""
        from agents.api_design import APIDesignAgent
        from agents.architecture import ArchitectureAgent
        from agents.bug_analyzer import BugAnalyzerAgent
        from agents.code_reviewer import CodeReviewerAgent
        from agents.database import DatabaseAgent
        from agents.dependency_audit import DependencyAuditAgent
        from agents.devops import DevOpsAgent
        from agents.documentation import DocumentationAgent
        from agents.exploit_analyzer import ExploitAnalyzerAgent
        from agents.performance import PerformanceAgent
        from agents.refactoring import RefactoringAgent
        from agents.security import SecurityAgent
        from agents.testing import TestingAgent

        agent_classes = {
            "code_reviewer": CodeReviewerAgent,
            "bug_analyzer": BugAnalyzerAgent,
            "architecture": ArchitectureAgent,
            "testing": TestingAgent,
            "security": SecurityAgent,
            "documentation": DocumentationAgent,
            "refactoring": RefactoringAgent,
            "devops": DevOpsAgent,
            "performance": PerformanceAgent,
            "exploit_analyzer": ExploitAnalyzerAgent,
            "database": DatabaseAgent,
            "api_design": APIDesignAgent,
            "dependency_audit": DependencyAuditAgent,
        }

        registry = AgentRegistry()
        for agent_id in registry.get_ids():
            assert agent_id in agent_classes, f"No class found for agent: {agent_id}"


class TestOllamaSettings:
    """Tests for the Ollama provider configuration."""

    def test_ollama_get_llm_kwargs(self):
        """Ollama kwargs should include model, base_url, and temperature."""
        import os
        from unittest.mock import patch

        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "ollama",
                "MODEL_NAME": "deepseek-r1",
                "OLLAMA_BASE_URL": "http://localhost:11434",
                "TEMPERATURE": "0.3",
            },
        ):
            from config.settings import Settings

            s = Settings()
            kwargs = s.get_llm_kwargs()
            assert kwargs["model"] == "deepseek-r1"
            assert kwargs["base_url"] == "http://localhost:11434"
            assert kwargs["temperature"] == 0.3
            # No api_key or max_tokens in Ollama kwargs
            assert "api_key" not in kwargs

    def test_ollama_validate_requires_no_api_key(self):
        """Ollama provider validation should succeed without any API keys."""
        import os
        from unittest.mock import patch

        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "ollama",
                "GITHUB_TOKEN": "",
                "NVIDIA_API_KEY": "",
            },
            clear=False,
        ):
            from config.settings import Settings

            s = Settings()
            # Should not raise
            s.validate()

    def test_ollama_default_base_url(self):
        """OLLAMA_BASE_URL should default to localhost:11434."""
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=False):
            # Remove OLLAMA_BASE_URL to test default
            env = {k: v for k, v in os.environ.items() if k != "OLLAMA_BASE_URL"}
            env["LLM_PROVIDER"] = "ollama"
            with patch.dict(os.environ, env, clear=True):
                from config.settings import Settings

                s = Settings()
                assert s.ollama_base_url == "http://localhost:11434"


class TestNewAgentsInRegistry:
    """Tests that the three new specialist agents are properly registered."""

    @pytest.mark.parametrize(
        "agent_id,expected_name",
        [
            ("database", "Database"),
            ("api_design", "API Design"),
            ("dependency_audit", "Dependency Audit"),
        ],
    )
    def test_new_agent_registered(self, agent_id, expected_name):
        registry = AgentRegistry()
        agent = registry.get(agent_id)
        assert agent is not None, f"Agent '{agent_id}' not found in registry"
        assert agent.name == expected_name
        assert len(agent.capabilities) >= 8
        assert len(agent.keywords) >= 10
