"""Sub agents that work with documents."""

import json
from collections.abc import AsyncGenerator
from pathlib import Path
from textwrap import dedent

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from injector import inject
from loguru import logger
from openfga_sdk import OpenFgaClient
from pydantic import ConfigDict

from src.agent.custom_types import (
    DocumentListArtifactKey,
    RetrieveContextKey,
    RowListArtifactKey,
)
from src.ofga_operations.checks import can_user_read


class RetrievalDocumentsAgent(BaseAgent):
    """Agent that mimicks the retrieval."""

    model_config = ConfigDict(extra="allow")

    @inject
    def __init__(
        self,
        documents_artifact_key: DocumentListArtifactKey,
        rows_artifact_key: RowListArtifactKey,
    ) -> None:
        """Init method."""
        super().__init__(
            name="retrieval_agent",
        )
        self._documents_artifact_key: DocumentListArtifactKey = documents_artifact_key
        self._rows_artifact_key: RowListArtifactKey = rows_artifact_key

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        if not ctx.artifact_service:
            raise RuntimeError()

        # Files are under the "data" folder. This is just for demo purposes.
        path = Path("data")
        document_path = path / "documents"

        paths = [doc.absolute() for doc in document_path.glob("*.txt")]
        path_2_contents = {}
        for p in paths:
            with p.open("r") as f:
                content = f.read()
                logger.debug("Retrieving {}. Length {}", p, len(content))
                path_2_contents[str(p.absolute())] = content

        await ctx.artifact_service.save_artifact(
            app_name=ctx.app_name,
            session_id=ctx.session.id,
            user_id=ctx.session.user_id,
            filename=self._documents_artifact_key,
            artifact=types.Part(text=json.dumps(path_2_contents)),
        )

        yield Event(
            author=self.name,
            custom_metadata={"retrieved_files": True, "has_error": False},
        )


class FilterDocumentAgent(BaseAgent):
    """Agent that filters the files using ofga api calls."""

    model_config = ConfigDict(extra="allow")

    @inject
    def __init__(
        self,
        openfga_client: OpenFgaClient,
        documents_artifact_key: DocumentListArtifactKey,
        rows_artifact_key: RowListArtifactKey,
        retrieved_context_key: RetrieveContextKey,
    ) -> None:
        """Init method."""
        super().__init__(
            name="filter_agent",
        )

        self._ofga_client: OpenFgaClient = openfga_client
        self._documents_artifact_key: DocumentListArtifactKey = documents_artifact_key
        self._rows_artifact_key: RowListArtifactKey = rows_artifact_key
        self._retrieved_context_key: RetrieveContextKey = retrieved_context_key

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
            filename=self._documents_artifact_key,
        )
        if not content or not content.text:
            raise RuntimeError()

        path_2_content: dict[str, str] = json.loads(content.text)
        filtered_path_2_content = {}
        for file_path_str, file_content in path_2_content.items():
            file_path = Path(file_path_str)
            file_name = file_path.name
            logger.info("Checking if user {} can read file {}", user_id, file_name)
            if await can_user_read(
                client=self._ofga_client, user_id=user_id, document_id=file_name
            ):
                logger.info("He/she can read file {}", file_name)
                filtered_path_2_content[str(file_path.absolute())] = file_content
        logger.info(filtered_path_2_content)
        await artifact_service.save_artifact(
            app_name=ctx.app_name,
            session_id=ctx.session.id,
            user_id=ctx.session.user_id,
            filename=self._retrieved_context_key,
            artifact=types.Part(text=json.dumps(filtered_path_2_content)),
        )

        yield Event(
            author=self.name,
            custom_metadata={"filtered_files": True, "has_error": False},
        )


class DocumentHandlerAgent(BaseAgent):
    """Agent that does RAG."""

    description: str = dedent("""
    Retrieves to-do items from the available documents.
    """)
    model_config = ConfigDict(extra="allow")

    @inject
    def __init__(
        self,
        _retriever_agent: RetrievalDocumentsAgent,
        _filter_agent: FilterDocumentAgent,
    ) -> None:
        """Init."""
        super().__init__(
            name="RAGAgent",
        )
        self._filter_agent = _filter_agent
        self._retriever_agent = _retriever_agent

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        logger.debug("Inside agent body.")
        data_retrieved_successfully: bool = False
        async for event in self._retriever_agent.run_async(ctx):
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

        async for event in self._filter_agent.run_async(ctx):
            event_metadata = event.custom_metadata
            if (
                event_metadata
                and "filtered_files" in event_metadata
                and event_metadata["filtered_files"]
                and "has_error" in event_metadata
                and not event_metadata["has_error"]
            ):
                logger.info("Data successfully filtered.")
            yield event
