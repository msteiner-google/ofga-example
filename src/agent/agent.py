"""Actual agent implementation."""

from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from injector import inject
from loguru import logger

from src.agent.custom_types import (
    AgentName,
    AnsweringAgent,
    DocumentListArtifactKey,
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


class OFGATestAgent(BaseAgent):
    """Custom agent."""

    retrieval_agent: RetrievalDocumentsAgent
    filter_agent: FilterDocumentAgent
    answering_agent: AnsweringAgent
    documents_artifact_key: DocumentListArtifactKey
    rows_artifact_key: RowListArtifactKey
    retrieved_context_key: RetrieveContextKey
    hr_data_agent: FilterTabularAgentDefaultDeny
    financial_data_agent: FilterTabulerAgentDefaultAllow

    @inject
    def __init__(  # noqa: PLR0913, PLR0917
        self,
        name: AgentName,
        retrieval_agent: RetrievalDocumentsAgent,
        filter_agent: FilterDocumentAgent,
        answering_agent: AnsweringAgent,
        documents_artifact_key: DocumentListArtifactKey,
        rows_artifact_key: RowListArtifactKey,
        retrieved_context_key: RetrieveContextKey,
        financial_data_agent: FilterTabulerAgentDefaultAllow,
        hr_data_agent: FilterTabularAgentDefaultDeny,
    ) -> None:
        """Init method."""
        super().__init__(
            name=name,
            filter_agent=filter_agent,
            retrieval_agent=retrieval_agent,
            answering_agent=answering_agent,
            documents_artifact_key=documents_artifact_key,
            rows_artifact_key=rows_artifact_key,
            retrieved_context_key=retrieved_context_key,
            hr_data_agent=hr_data_agent,
            financial_data_agent=financial_data_agent,
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        logger.debug("Inside agent body.")
        data_retrieved_successfully: bool = False
        async for event in self.retrieval_agent.run_async(ctx):
            event_metadata = event.custom_metadata
            if event_metadata:
                logger.info("Event has metadata.")
                if (
                    event_metadata["retrieved_files"]
                    and not event_metadata["has_error"]
                ):
                    data_retrieved_successfully = True
        if data_retrieved_successfully:
            logger.info("data was retrieved!")

        async for event in self.filter_agent.run_async(ctx):
            event_metadata = event.custom_metadata
            if (
                event_metadata
                and "filtered_files" in event_metadata
                and event_metadata["filtered_files"]
                and "has_error" in event_metadata
                and not event_metadata["has_error"]
            ):
                logger.info("Data successfully filtered.")

        async for event in self.answering_agent.run_async(ctx):
            yield event
