"""Agents for tabular data."""

import json
from collections.abc import AsyncGenerator
from sqlite3 import Connection, Cursor
from textwrap import dedent

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.runners import InvocationContext
from google.genai import types
from loguru import logger
from openfga_sdk import OpenFgaClient
from pydantic import ConfigDict

from src.agent.custom_types import FinancialDataConnection, HRDataConnection
from src.ofga_operations.objects import list_objects_for_user
from src.project_types import ACLType


class _FilteringTabularAgentLike(BaseAgent):
    """Agent that pulls of the tabular data while performing pre-filtering."""

    model_config = ConfigDict(extra="allow")

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        acl_type: ACLType,
        sqlite_conn: Connection,
        ofga_client: OpenFgaClient,
        relationships_name: str,
        name: str,
        description: str,
    ) -> None:
        """Init method.

        Args:
            acl_type (ACLType): The type of ACL this tabular agent will use when
                                building the query.
            sqlite_conn (Connection): The connection with the data.
            ofga_client (OpenFgaClient): The openfga client that will be used to perform
                the ListObject api requests.
            relationships_name(str): The name of the relationships in ofga.
            name(str): The name of the agent.
            description(str): The purpose of this agent.
        """
        super().__init__(
            name=name,
            description=description,
        )

        self._acl_type: ACLType = acl_type
        self._sqlite_connection: Connection = sqlite_conn
        self._ofga_client: OpenFgaClient = ofga_client
        self._relationships_name: str = relationships_name

    async def _build_query(self, user_id: str) -> str:
        object_type = "item"
        objects = await list_objects_for_user(
            user_id=user_id,
            relation=self._relationships_name,
            object_type=object_type,
            client=self._ofga_client,
        )
        objects = [f'"{o.split(":")[-1]}"' for o in objects]
        logger.info("ListObject for user {} returned: {}", user_id, objects)
        clause = "IN" if self._acl_type == ACLType.DEFAULT_DENY else "NOT IN"

        query = dedent(f"""
        SELECT * FROM data
        WHERE data.id {clause} ({",".join(objects)})
        """)  # noqa: S608
        logger.info("Query {}", query)
        return query

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        if not ctx.artifact_service:
            raise RuntimeError()

        query = await self._build_query(user_id=ctx.user_id)
        cur: Cursor = self._sqlite_connection.execute(query)

        data = json.dumps(cur.fetchall())
        logger.info(data)
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=data)]),
        )


class FilterTabularAgentDefaultDeny(_FilteringTabularAgentLike):
    """Pass."""

    def __init__(
        self, connection: HRDataConnection, ofga_client: OpenFgaClient, description: str
    ) -> None:
        """Something."""
        super().__init__(
            name="HRAgent",
            acl_type=ACLType.DEFAULT_DENY,
            ofga_client=ofga_client,
            sqlite_conn=connection,
            relationships_name="can_read",
            description=description,
        )


class FilterTabulerAgentDefaultAllow(_FilteringTabularAgentLike):
    """Pass."""

    def __init__(
        self,
        connection: FinancialDataConnection,
        ofga_client: OpenFgaClient,
        description: str,
    ) -> None:
        """Something."""
        super().__init__(
            name="FinancialAgent",
            acl_type=ACLType.DEFAULT_ALLOW_WITH_EXPLICIT_DENY,
            ofga_client=ofga_client,
            sqlite_conn=connection,
            relationships_name="excluded",
            description=description,
        )
