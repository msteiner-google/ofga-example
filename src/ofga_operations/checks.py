"""Methods to perform checks."""

from typing import TYPE_CHECKING, cast

from openfga_sdk import OpenFgaClient
from openfga_sdk.client import ClientCheckRequest

if TYPE_CHECKING:
    from openfga_sdk.models.check_response import CheckResponse


async def can_user_read(
    client: OpenFgaClient,
    user_id: str,
    document_id: str,
    relation: str = "can_read",
    object_type: str = "item",
) -> bool:
    """Checks if a user can read the given file."""
    check_request = ClientCheckRequest(
        user=f"user:{user_id}", relation=relation, object=f"{object_type}:{document_id}"
    )
    result: CheckResponse = cast("CheckResponse", await client.check(check_request))

    return bool(result.allowed)
