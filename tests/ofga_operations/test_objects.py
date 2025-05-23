"""Tests objects."""

from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from openfga_sdk import OpenFgaClient
from openfga_sdk.client.models.list_objects_request import ClientListObjectsRequest

from src.ofga_operations.objects import list_objects_for_user


@pytest_asyncio.fixture
async def mock_openfga_client() -> AsyncMock:  # noqa: D103, RUF029
    return AsyncMock(spec=OpenFgaClient)


@pytest.mark.asyncio
async def test_list_objects_for_user(mock_openfga_client: AsyncMock) -> None:
    """Test basic functionalities."""
    user_id = "anne"
    relation = "viewer"
    object_type = "document"
    expected_objects = ["doc:readme", "doc:roadmap"]

    mock_response = MagicMock()
    mock_response.objects = expected_objects
    mock_openfga_client.list_objects.return_value = mock_response

    result = await list_objects_for_user(
        user_id=user_id,
        relation=relation,
        object_type=object_type,
        client=mock_openfga_client,
    )

    expected_request = ClientListObjectsRequest(
        user=f"user:{user_id}", relation=relation, type=object_type
    )

    mock_openfga_client.list_objects.assert_awaited_once()
    # Check the call arguments. Since ClientListObjectsRequest may not implement
    # __eq__ by default for all fields,
    # we can check its attributes individually or ensure it's called with an instance
    # of the class. For a more robust check, you might need to ensure the fields of the
    # passed request match.
    args, _ = mock_openfga_client.list_objects.call_args
    assert isinstance(args[0], ClientListObjectsRequest)
    assert args[0].user == expected_request.user
    assert args[0].relation == expected_request.relation
    assert args[0].type == expected_request.type

    assert result == expected_objects
