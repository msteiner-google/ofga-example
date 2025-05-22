"""Operations relative to the store."""

import asyncio
import json
from typing import TYPE_CHECKING, cast

import openfga_sdk
from loguru import logger
from openfga_sdk.models.create_store_request import CreateStoreRequest
from openfga_sdk.models.create_store_response import CreateStoreResponse
from openfga_sdk.models.write_authorization_model_request import (
    WriteAuthorizationModelRequest,
)

from src.configuration.configuration_model import (
    GeneralConfiguration,
    OFGAStoreConfiguration,
)
from src.ofga_operations.utils import get_client
from src.project_types import OFGASecurityModel

if TYPE_CHECKING:
    from openfga_sdk.models import WriteAuthorizationModelResponse


async def get_or_create_store(
    store_configuration: OFGAStoreConfiguration, client: openfga_sdk.OpenFgaClient
) -> CreateStoreResponse:
    """Gets or create a store.

    In the OpenFGA apis there is no distiction. If a store exists already and you try
    to create it again you get back the same metadata. Proof of that is that there is no
    `GetStoreRequest` in the
    [metadata](https://github.com/openfga/python-sdk/blob/main/README.md#documentation-for-models)
    """
    try:
        body = CreateStoreRequest(name=store_configuration.store_name)
        response: CreateStoreResponse = cast(
            "CreateStoreResponse", await client.create_store(body)
        )
        logger.info("Create store response: {store}", store=response)
    except Exception:
        logger.exception("Error getting/creating store.")
        raise
    else:
        return response


async def write_authorization_id(
    auth_model_definition: OFGASecurityModel,
    client: openfga_sdk.OpenFgaClient,
) -> openfga_sdk.WriteAuthorizationModelResponse:
    """Writes an authorization model to the store."""
    try:
        logger.info("auth model: {data}", data=json.dumps(auth_model_definition))
        body = WriteAuthorizationModelRequest(**auth_model_definition)
        raw_response = await client.write_authorization_model(body)
        logger.info("{}", raw_response)
        response: WriteAuthorizationModelResponse = cast(
            "WriteAuthorizationModelResponse", raw_response
        )

    except Exception:
        logger.exception("What?")
        raise
    else:
        return response
