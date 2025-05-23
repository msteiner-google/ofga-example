"""Dependency injection."""

from textwrap import dedent
from typing import override

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.runners import (
    BaseArtifactService,
    InMemoryArtifactService,
    InMemorySessionService,
    Runner,
)
from google.adk.sessions import BaseSessionService
from injector import Binder, Module, provider, singleton

from src.agent.agent import OFGATestAgent
from src.agent.custom_types import (
    AgentName,
    AnsweringAgent,
    AppName,
    DocumentListArtifactKey,
    GeminiModel,
    RetrieveContextKey,
    RowListArtifactKey,
)
from src.agent.sub_agents.document_agents import (
    FilterDocumentAgent,
    RetrievalDocumentsAgent,
)
from src.agent.sub_agents.tabular_agent import (
    FilterTabularAgentDefaultDeny,
    FilterTabulerAgentDefaultAllow,
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
    def _provide_agent(  # noqa: PLR0913, PLR0917, PLR6301
        self,
        agent_name: AgentName,
        retrieval_agent: RetrievalDocumentsAgent,
        filter_agent: FilterDocumentAgent,
        documents_artifact_key: DocumentListArtifactKey,
        rows_artifact_key: RowListArtifactKey,
        answering_agent: AnsweringAgent,
        retrieved_context_key: RetrieveContextKey,
        hr_agent: FilterTabularAgentDefaultDeny,
        financial_data_agent: FilterTabulerAgentDefaultAllow,
    ) -> BaseAgent:
        return OFGATestAgent(
            name=agent_name,
            retrieval_agent=retrieval_agent,
            filter_agent=filter_agent,
            answering_agent=answering_agent,
            documents_artifact_key=documents_artifact_key,
            rows_artifact_key=rows_artifact_key,
            retrieved_context_key=retrieved_context_key,
            financial_data_agent=financial_data_agent,
            hr_data_agent=hr_agent,
        )

    @provider
    @singleton
    def _provde_artifact_service(self) -> BaseArtifactService:  # noqa: PLR6301
        return InMemoryArtifactService()

    @provider
    @singleton
    def _provide_answering_agent(  # noqa: PLR6301
        self, model: GeminiModel, retrieved_context_key: RetrieveContextKey
    ) -> AnsweringAgent:
        llm_agent = LlmAgent(
            name="answering_agent",
            model=model,
            description="Agent that formats the final answer for the user.",
            instruction=dedent(f"""
            You are an helpful assistant.

            You use reply to the user question using the following context.

            Context:
            ```
            {{artifact.{retrieved_context_key}}}
            ```

            Question:
            ```
            {{last_question}}
            ```
            """),
        )
        return AnsweringAgent(llm_agent)

    @override
    def configure(self, binder: Binder) -> None:
        """Define simple bindings."""
        binder.bind(DocumentListArtifactKey, to=DocumentListArtifactKey("documents"))
        binder.bind(RowListArtifactKey, to=RowListArtifactKey("rows"))
        binder.bind(RetrieveContextKey, to=RetrieveContextKey("retrieved_context"))
