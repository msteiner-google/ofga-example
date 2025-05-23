"""DI module for the sub-agents."""

import sqlite3
from pathlib import Path

import pandas as pd
from injector import Module, provider, singleton
from loguru import logger
from openfga_sdk import OpenFgaClient

from src.agent.custom_types import (
    DocumentListArtifactKey,
    FinancialDataConnection,
    HRDataConnection,
    RetrieveContextKey,
    RowListArtifactKey,
)
from src.agent.sub_agents.document_agents import FilterDocumentAgent
from src.agent.sub_agents.tabular_agent import (
    FilterTabularAgentDefaultDeny,
    FilterTabulerAgentDefaultAllow,
)


class SubAgentModule(Module):
    """Wiring."""

    @provider
    @singleton
    def _provide_filter_agent(  # noqa: PLR6301
        self,
        clients: dict[str, OpenFgaClient],
        documents_artifact_key: DocumentListArtifactKey,
        rows_artifact_key: RowListArtifactKey,
        retrieved_context_key: RetrieveContextKey,
    ) -> FilterDocumentAgent:
        # WARN: This shouldn't be hardcoded.
        logger.info("Client keys: {}", list(clients.keys()))
        client = clients["store_for_documents_configuration"]
        return FilterDocumentAgent(
            openfga_client=client,
            documents_artifact_key=documents_artifact_key,
            rows_artifact_key=rows_artifact_key,
            retrieved_context_key=retrieved_context_key,
        )

    @provider
    @singleton
    def _provide_hr_data(self) -> HRDataConnection:  # noqa: PLR6301
        path = Path("data/tabular_data/hr_data.csv")
        if not path.exists():
            logger.error("Path {} does not exists.", str(path.absolute()))
            raise RuntimeError()

        df = pd.read_csv(str(path.absolute()))  # noqa: PD901
        # In memory connection for example.
        connection = sqlite3.connect(":memory:")

        df.to_sql(name="data", con=connection, if_exists="replace", index=False)
        return HRDataConnection(connection)

    @provider
    @singleton
    def _provide_financial_data(self) -> FinancialDataConnection:  # noqa: PLR6301
        path = Path("data/tabular_data/financial_data.csv")
        if not path.exists():
            logger.error("Path {} does not exists.", str(path.absolute()))
            raise RuntimeError()

        df = pd.read_csv(str(path.absolute()))  # noqa: PD901
        # In memory connection for example.
        connection = sqlite3.connect(":memory:")

        df.to_sql(name="data", con=connection, if_exists="replace", index=False)
        return FinancialDataConnection(connection)

    @provider
    @singleton
    def _provide_agent_for_financial_data(  # noqa: PLR6301
        self,
        db_conn: HRDataConnection,
        clients: dict[str, OpenFgaClient],
    ) -> FilterTabulerAgentDefaultAllow:
        # WARN: This shouldn't be hardcoded.
        client = clients["store_for_tables_with_default_allow"]
        return FilterTabulerAgentDefaultAllow(connection=db_conn, client=client)

    @provider
    @singleton
    def _provide_agent_for_hr_data(  # noqa: PLR6301
        self,
        db_conn: HRDataConnection,
        clients: dict[str, OpenFgaClient],
    ) -> FilterTabularAgentDefaultDeny:
        # WARN: This shouldn't be hardcoded.
        client = clients["store_for_tables_with_default_deny"]
        return FilterTabularAgentDefaultDeny(connection=db_conn, client=client)
