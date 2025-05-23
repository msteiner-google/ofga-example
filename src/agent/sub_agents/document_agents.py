"""Sub agents that work with documents."""

import json
from collections.abc import AsyncGenerator
from pathlib import Path

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from injector import inject
from loguru import logger
from openfga_sdk import OpenFgaClient

from src.agent.custom_types import (
    DocumentListArtifactKey,
    RetrieveContextKey,
    RowListArtifactKey,
)
from src.ofga_operations.checks import can_user_read


class RetrievalDocumentsAgent(BaseAgent):
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
            filename=self.documents_artifact_key,
            artifact=types.Part(text=json.dumps(path_2_contents)),
        )

        yield Event(
            author=self.name,
            custom_metadata={"retrieved_files": True, "has_error": False},
        )


class FilterDocumentAgent(BaseAgent):
    """Agent that filters the files using ofga api calls."""

    ofga_client: OpenFgaClient
    documents_artifact_key: DocumentListArtifactKey
    rows_artifact_key: RowListArtifactKey
    retrieved_context_key: RetrieveContextKey

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
            ofga_client=openfga_client,
            documents_artifact_key=documents_artifact_key,
            rows_artifact_key=rows_artifact_key,
            retrieved_context_key=retrieved_context_key,
        )

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
            if await can_user_read(
                client=self.ofga_client, user_id=user_id, document_id=file_name
            ):
                logger.info("He/she can read file {}", file_name)
                filtered_path_2_content[str(file_path.absolute())] = file_content
        logger.info(filtered_path_2_content)
        await artifact_service.save_artifact(
            app_name=ctx.app_name,
            session_id=ctx.session.id,
            user_id=ctx.session.user_id,
            filename=self.retrieved_context_key,
            artifact=types.Part(text=json.dumps(filtered_path_2_content)),
        )

        yield Event(
            author=self.name,
            custom_metadata={"filtered_files": True, "has_error": False},
        )
