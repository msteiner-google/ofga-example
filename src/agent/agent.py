"""Actual agent implementation."""

# type: ignore[reportCallIssue]

from collections.abc import AsyncGenerator
from typing import override

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types
from injector import inject
from loguru import logger
from openfga_sdk import OpenFgaClient

from src.agent.custom_types import (
    AgentName,
    DocumentListArtifactKey,
    RowListArtifactKey,
)


class _RetrievalAgent(BaseAgent):
    """Agent that mimicks the retrieval."""

    documents_artifact_key: DocumentListArtifactKey
    rows_artifact_key: RowListArtifactKey

    @inject
    def __init__(
        self,
        documents_artifact_key: DocumentListArtifactKey,
        rows_artifact_key: RowListArtifactKey,
    ) -> None:
        """Init method."""
        super().__init__(
            name="retrieval_agent",
            documents_artifact_key=documents_artifact_key,
            rows_artifact_key=rows_artifact_key,
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        yield Event(author=self.name)


class _FilterAgent(BaseAgent):
    """Agent that filters the files using ofga api calls."""

    ofga_client: OpenFgaClient
    documents_artifact_key: DocumentListArtifactKey
    rows_artifact_key: RowListArtifactKey

    @inject
    def __init__(
        self,
        openfga_client: OpenFgaClient,
        documents_artifact_key: DocumentListArtifactKey,
        rows_artifact_key: RowListArtifactKey,
    ) -> None:
        """Init method."""
        super().__init__(
            name="filter_agent",
            ofga_client=openfga_client,
            documents_artifact_key=documents_artifact_key,
            rows_artifact_key=rows_artifact_key,
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        yield Event(author=self.name)


class OFGATestAgent(BaseAgent):
    """Custom agent."""

    retrieval_agent: _RetrievalAgent
    filter_agent: _FilterAgent
    documents_artifact_key: DocumentListArtifactKey
    rows_artifact_key: RowListArtifactKey

    @inject
    def __init__(
        self,
        name: AgentName,
        retrieval_agent: _RetrievalAgent,
        filter_agent: _FilterAgent,
        documents_artifact_key: DocumentListArtifactKey,
        rows_artifact_key: RowListArtifactKey,
    ) -> None:
        """Init method."""
        super().__init__(
            name=name,
            filter_agent=filter_agent,
            retrieval_agent=retrieval_agent,
            documents_artifact_key=documents_artifact_key,
            rows_artifact_key=rows_artifact_key,
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        for event in ctx.session.events:
            logger.info("{}", event)

        reply = types.Content(role="agent", parts=[types.Part(text="Canned response")])
        state_change = {
            "user_visible_messages": ctx.session.state["user_visible_messages"]
            + ["test"]
        }
        actions_with_update = EventActions(state_delta=state_change)
        system_event = Event(
            invocation_id="test_update", author="system", actions=actions_with_update
        )
        ctx.session_service.append_event(ctx.session, system_event)

        logger.info(ctx.session.state)
        yield Event(author="agent", content=reply)
