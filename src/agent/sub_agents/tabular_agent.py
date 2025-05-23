"""Agents for tabular data."""

from collections.abc import AsyncGenerator
from enum import Enum
from sqlite3 import Connection
from textwrap import dedent

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.adk.runners import InvocationContext
from injector import inject
from loguru import logger
from openfga_sdk import OpenFgaClient
from pydantic import ConfigDict

from src.agent.custom_types import FinancialDataConnection, HRDataConnection
from src.ofga_operations.objects import list_objects_for_user
from src.project_types import ACLType


class _ShouldItemBeKept(Enum):
    YES = 0
    NO = 1


class _FilteringTabularAgentLike(BaseAgent):
    """Agent that pulls of the tabular data while performing pre-filtering."""

    _acl_type: ACLType
    _sqlite_connection: Connection
    _ofga_client: OpenFgaClient
    _relationships_name: str
    model_config = ConfigDict(extra="allow")

    def __init__(
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
            _acl_type=acl_type,
            _sqlite_connection=sqlite_conn,
            _ofga_client=ofga_client,
            _relationships_name=relationships_name,
            name=name,
            description=description,
        )

    def _handle_relationship_being_present(
        self,
        is_relationship_present: bool,  # noqa: FBT001
    ) -> _ShouldItemBeKept:
        # If the acl type is DEFAULT_DENY and the relationship is present it means that
        # we should keep the item.
        if self._acl_type == ACLType.DEFAULT_DENY and is_relationship_present:
            return _ShouldItemBeKept.YES

        # If the ACL type is default allow and there is no relationship it means the
        # user isn't blacklisted and so the item should be kept.
        if (
            self._acl_type == ACLType.DEFAULT_ALLOW_WITH_EXPLICIT_DENY
            and not is_relationship_present
        ):
            return _ShouldItemBeKept.YES

        # We should return no in all other cases.
        return _ShouldItemBeKept.NO

    async def _build_query(self, user_id: str) -> str:
        object_type = "item"
        objects = list_objects_for_user(
            user_id=user_id,
            relation=self._relationships_name,
            object_type=object_type,
            client=self._ofga_client,
        )
        logger.info("ListObject for user {} returned: {}", user_id, objects)
        return dedent("""
        SELECT * FROM data
        WHERE TRUE
        """)

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        if not ctx.artifact_service:
            raise RuntimeError()

        # Files are under the "data" folder. This is just for demo purposes.

        yield Event(
            author=self.name,
            custom_metadata={"retrieved_files": False, "has_error": False},
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
