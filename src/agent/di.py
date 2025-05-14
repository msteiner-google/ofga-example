"""Dependency injection."""

from typing import override

from google.adk.agents import BaseAgent
from google.adk.runners import (
    BaseArtifactService,
    InMemoryArtifactService,
    InMemorySessionService,
    Runner,
)
from google.adk.sessions import BaseSessionService
from injector import Binder, Module, provider, singleton

from src.agent.agent import OFGATestAgent, _FilterAgent, _RetrievalAgent
from src.agent.custom_types import (
    AgentName,
    AppName,
    DocumentListArtifactKey,
    RowListArtifactKey,
)


class AgentModule(Module):
    """Module for wiring Agent dependencies."""

    @provider
    @singleton
    def _provide_adk_runner(  # noqa: PLR6301
        self,
        agent: BaseAgent,
        app_name: AppName,
        session_service: BaseSessionService,
        artifact_service: BaseArtifactService,
    ) -> Runner:
        return Runner(
            agent=agent,
            app_name=app_name,
            session_service=session_service,
            artifact_service=artifact_service,
        )

    @provider
    @singleton
    def _provide_session_service(self) -> BaseSessionService:  # noqa: PLR6301
        return InMemorySessionService()

    @provider
    @singleton
    def _provide_agent(  # noqa: PLR6301
        self,
        agent_name: AgentName,
        retrieval_agent: _RetrievalAgent,
        filter_agent: _FilterAgent,
        documents_artifact_key: DocumentListArtifactKey,
        rows_artifact_key: RowListArtifactKey,
    ) -> BaseAgent:
        return OFGATestAgent(
            name=agent_name,
            retrieval_agent=retrieval_agent,
            filter_agent=filter_agent,
            documents_artifact_key=documents_artifact_key,
            rows_artifact_key=rows_artifact_key,
        )

    @provider
    @singleton
    def _provde_artifact_service(self) -> BaseArtifactService:  # noqa: PLR6301
        return InMemoryArtifactService()

    @override
    def configure(self, binder: Binder) -> None:
        """Define simple bindings."""
        binder.bind(DocumentListArtifactKey, to=DocumentListArtifactKey("documents"))
        binder.bind(RowListArtifactKey, to=RowListArtifactKey("rows"))
