"""Operations relative to the store."""

from typing import cast

import openfga_sdk
from loguru import logger
from openfga_sdk.client import OpenFgaClient
from openfga_sdk.models.create_store_request import CreateStoreRequest
from openfga_sdk.models.create_store_response import CreateStoreResponse

from configuration.configuration_model import GeneralConfiguration


def _get_or_create_client(
    configuration: GeneralConfiguration, openfga_client: OpenFgaClient | None
) -> OpenFgaClient:
    if openfga_client:
        return openfga_client
    client_configuration = openfga_sdk.ClientConfiguration(
        api_url=configuration.server_configuration.api_url
    )
    return OpenFgaClient(client_configuration)


async def get_or_create_store(
    configuration: GeneralConfiguration, openfga_client: OpenFgaClient | None = None
) -> CreateStoreResponse:
    """Gets or create a store.

    In the OpenFGA apis there is no distiction. If a store exists already and you try
    to create it again you get back the same metadata. Proof of that is that there is no
    `GetStoreRequest` in the
    [metadata](https://github.com/openfga/python-sdk/blob/main/README.md#documentation-for-models)
    """
    client = _get_or_create_client(configuration, openfga_client)
    body = CreateStoreRequest(name=configuration.store_configuration.store_name)
    response: CreateStoreResponse = cast(
        "CreateStoreResponse", await client.create_store(body)
    )
    logger.info("Create store response: {store}", store=response)
    if not openfga_client:
        await client.close()
    return response
