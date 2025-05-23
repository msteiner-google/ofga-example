"""Utility methods that target objects."""

from loguru import logger
from openfga_sdk import OpenFgaClient
from openfga_sdk.client.models.list_objects_request import ClientListObjectsRequest


async def list_objects_for_user(
    user_id: str, relation: str, object_type: str, client: OpenFgaClient
) -> list[str]:
    """Performs a list objects request."""
    logger.debug("user_id {}, relation {}, type {}", user_id, relation, object_type)
    req = ClientListObjectsRequest(
        user=f"user:{user_id}", relation=relation, type=object_type
    )
    raw_response = await client.list_objects(req)
    return raw_response.objects  # type: ignore
