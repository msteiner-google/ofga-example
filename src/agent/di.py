"""Dependency injection."""

from google.adk.agents import BaseAgent
from google.adk.runners import InMemorySessionService, Runner
from google.adk.sessions import BaseSessionService
from injector import Module, provider, singleton

from src.agent.agent import OFGATestAgent
from src.agent.custom_types import AgentName, AppName


class AgentModule(Module):
    """Module for wiring Agent dependencies."""

    @provider
    @singleton
    def _provide_adk_runner(  # noqa: PLR6301
        self, agent: BaseAgent, app_name: AppName, session_service: BaseSessionService
    ) -> Runner:
        return Runner(agent=agent, app_name=app_name, session_service=session_service)

    @provider
    @singleton
    def _provide_session_service(self) -> BaseSessionService:  # noqa: PLR6301
        return InMemorySessionService()

    @provider
    @singleton
    def _provide_agent(self, agent_name: AgentName) -> BaseAgent:  # noqa: PLR6301
        return OFGATestAgent(name=agent_name)
