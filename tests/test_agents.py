"""Tests for specialist agents and base agent."""

from unittest.mock import patch

import pytest


class TestBaseAgentInterface:
    """Verify that all agents implement the required interface."""

    @pytest.fixture(
        params=[
            "agents.code_reviewer.CodeReviewerAgent",
            "agents.bug_analyzer.BugAnalyzerAgent",
            "agents.architecture.ArchitectureAgent",
            "agents.testing.TestingAgent",
            "agents.security.SecurityAgent",
            "agents.documentation.DocumentationAgent",
            "agents.refactoring.RefactoringAgent",
            "agents.devops.DevOpsAgent",
            "agents.performance.PerformanceAgent",
            "agents.exploit_analyzer.ExploitAnalyzerAgent",
            "agents.database.DatabaseAgent",
            "agents.api_design.APIDesignAgent",
            "agents.dependency_audit.DependencyAuditAgent",
        ]
    )
    def agent_class_path(self, request):
        return request.param

    def _import_agent_class(self, path: str):
        """Dynamically import an agent class from its dotted path."""
        module_path, class_name = path.rsplit(".", 1)
        import importlib

        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    @patch("agents.base_agent.create_chat_model")
    def test_agent_has_system_prompt(self, mock_llm, agent_class_path):
        """Each agent must return a non-empty system prompt."""
        cls = self._import_agent_class(agent_class_path)
        agent = cls()
        prompt = agent.get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100, f"{cls.__name__} system prompt is too short"

    @patch("agents.base_agent.create_chat_model")
    def test_agent_has_id_and_name(self, mock_llm, agent_class_path):
        """Each agent must have a non-empty ID and name."""
        cls = self._import_agent_class(agent_class_path)
        agent = cls()
        assert agent.agent_id, f"{cls.__name__} has no agent_id"
        assert agent.name, f"{cls.__name__} has no name"

    @patch("agents.base_agent.create_chat_model")
    def test_agent_repr(self, mock_llm, agent_class_path):
        """Each agent should have a useful repr."""
        cls = self._import_agent_class(agent_class_path)
        agent = cls()
        repr_str = repr(agent)
        assert agent.agent_id in repr_str
        assert agent.name in repr_str

    @patch("agents.base_agent.create_chat_model")
    def test_format_output_structure(self, mock_llm, agent_class_path):
        """format_output should return a dict with required keys including severity."""
        cls = self._import_agent_class(agent_class_path)
        agent = cls()
        output = agent.format_output(
            task_description="Test task",
            result="Test result",
            status="success",
        )
        assert output["agent_id"] == agent.agent_id
        assert output["agent_name"] == agent.name
        assert output["task_description"] == "Test task"
        assert output["result"] == "Test result"
        assert output["status"] == "success"
        assert "severity_summary" in output
        assert "overall" in output["severity_summary"]
        assert "total_findings" in output["severity_summary"]


class TestAgentPrompts:
    """Verify that all prompt modules are properly defined."""

    @pytest.mark.parametrize(
        "prompt_module,prompt_var",
        [
            ("prompts.orchestrator_prompt", "ORCHESTRATOR_SYSTEM_PROMPT"),
            ("prompts.code_reviewer_prompt", "CODE_REVIEWER_SYSTEM_PROMPT"),
            ("prompts.bug_analyzer_prompt", "BUG_ANALYZER_SYSTEM_PROMPT"),
            ("prompts.architecture_prompt", "ARCHITECTURE_SYSTEM_PROMPT"),
            ("prompts.testing_prompt", "TESTING_SYSTEM_PROMPT"),
            ("prompts.security_prompt", "SECURITY_SYSTEM_PROMPT"),
            ("prompts.documentation_prompt", "DOCUMENTATION_SYSTEM_PROMPT"),
            ("prompts.refactoring_prompt", "REFACTORING_SYSTEM_PROMPT"),
            ("prompts.devops_prompt", "DEVOPS_SYSTEM_PROMPT"),
            ("prompts.performance_prompt", "PERFORMANCE_SYSTEM_PROMPT"),
            ("prompts.exploit_analyzer_prompt", "EXPLOIT_ANALYZER_SYSTEM_PROMPT"),
            ("prompts.database_prompt", "DATABASE_SYSTEM_PROMPT"),
            ("prompts.api_design_prompt", "API_DESIGN_SYSTEM_PROMPT"),
            ("prompts.dependency_audit_prompt", "DEPENDENCY_AUDIT_SYSTEM_PROMPT"),
        ],
    )
    def test_prompt_exists_and_is_substantial(self, prompt_module, prompt_var):
        """Each prompt module should export a substantial system prompt."""
        import importlib

        module = importlib.import_module(prompt_module)
        prompt = getattr(module, prompt_var)
        assert isinstance(prompt, str)
        assert len(prompt) > 200, f"{prompt_module}.{prompt_var} is too short ({len(prompt)} chars)"
