"""Main for creating a store."""

import asyncio
from typing import TYPE_CHECKING, cast

import openfga_sdk
from loguru import logger
from openfga_sdk.client import OpenFgaClient
from openfga_sdk.models.create_store_request import CreateStoreRequest

from configuration.configuration_model import (
    OpenFGAServerConfiguration,
    StoreConfiguration,
)

if TYPE_CHECKING:
    from openfga_sdk.models.create_store_response import CreateStoreResponse


async def _main() -> None:
    configuration = OpenFGAServerConfiguration()
    store_config = StoreConfiguration()
    logger.info("{store}", store=store_config)
    openfga_client_configuration = openfga_sdk.ClientConfiguration(
        api_url=configuration.api_url,
    )
    async with OpenFgaClient(openfga_client_configuration) as fga_client:
        body = CreateStoreRequest(
            name=store_config.store_name,
        )
        response: CreateStoreResponse = cast(
            "CreateStoreResponse", await fga_client.create_store(body)
        )

        logger.info("Operation response: {response}", response=response)


def entrypoint() -> None:
    """Actual entrypoint."""
    asyncio.run(_main())
