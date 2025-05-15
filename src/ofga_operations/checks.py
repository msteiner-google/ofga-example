"""Methods to perform checks."""

from typing import TYPE_CHECKING, cast

from openfga_sdk import OpenFgaClient
from openfga_sdk.client import ClientCheckRequest

if TYPE_CHECKING:
    from openfga_sdk.models.check_response import CheckResponse


async def can_user_read(user_id: str, document_id: str, client: OpenFgaClient) -> bool:
    """Checks if a user can read the given file."""
    check_request = ClientCheckRequest(
        user=f"user:{user_id}", relation="can_read", object=f"doc:{document_id}"
    )
    result: CheckResponse = cast("CheckResponse", await client.check(check_request))

    return bool(result.allowed)
