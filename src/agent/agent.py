"""Actual agent implementation."""

# type: ignore[reportCallIssue]

import json
from collections.abc import AsyncGenerator
from pathlib import Path
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
from src.ofga_operations.checks import can_user_read


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
        if not ctx.artifact_service:
            raise RuntimeError()

        # TODO: pass this as part of the configuration.
        path = Path("data")
        document_path = path / "documents"

        paths = [doc.absolute() for doc in document_path.glob("*.txt")]
        path_2_contents = {}
        for p in paths:
            with p.open("r") as f:
                content = f.read()
                logger.debug("Retrieving {}. Length {}", p, len(content))
                path_2_contents[str(p.absolute())] = f.read()

        await ctx.artifact_service.save_artifact(
            app_name=ctx.app_name,
            session_id=ctx.session.id,
            user_id=ctx.session.user_id,
            filename=self.documents_artifact_key,
            artifact=types.Part(text=json.dumps(path_2_contents)),
        )

        yield Event(
            author=self.name,
            custom_metadata={"retrieved_files": True, "has_error": False},
        )


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
        super().__init__(  # type: ignore
            name="filter_agent",
            ofga_client=openfga_client,
            documents_artifact_key=documents_artifact_key,
            rows_artifact_key=rows_artifact_key,
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        artifact_service = ctx.artifact_service
        if not artifact_service:
            raise RuntimeError()

        user_id = ctx.session.user_id
        content = await artifact_service.load_artifact(
            app_name=ctx.app_name,
            session_id=ctx.session.id,
            user_id=user_id,
            filename=self.documents_artifact_key,
        )
        if not content or not content.text:
            raise RuntimeError()

        path_2_content: dict[str, str] = json.loads(content.text)
        filtered_path_2_content = {}
        for file_path_str, file_content in path_2_content.items():
            file_path = Path(file_path_str)
            file_name = file_path.name
            logger.info("Checking if user {} can read file {}", user_id, file_name)
            if await can_user_read(user_id, file_name, self.ofga_client):
                logger.info("He/she can read file {}", file_name)
                filtered_path_2_content[str(file_path.absolute())] = file_content

        await artifact_service.save_artifact(
            app_name=ctx.app_name,
            session_id=ctx.session.id,
            user_id=ctx.session.user_id,
            filename=self.documents_artifact_key,
            artifact=types.Part(text=json.dumps(filtered_path_2_content)),
        )

        yield Event(
            author=self.name,
            custom_metadata={"filtered_files": True, "has_error": False},
        )


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
            if event_metadata:
                logger.debug("Event has metadata")
                if event_metadata["filtered_files"] and not event_metadata["has_error"]:
                    logger.info("Data successfully filtered.")

        yield Event(
            author="agent", content=types.Content(parts=[types.Part(text="ran")])
        )
