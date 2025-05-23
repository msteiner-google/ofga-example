"""Tests on check operations."""

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from openfga_sdk import OpenFgaClient
from openfga_sdk.client import ClientCheckRequest
from openfga_sdk.models.check_response import CheckResponse

from src.ofga_operations.checks import can_user_read


@pytest_asyncio.fixture
async def mock_openfga_client() -> AsyncMock:  # noqa: RUF029
    """Fixture to create a mock OpenFgaClient."""
    return AsyncMock(spec=OpenFgaClient)


@pytest.mark.asyncio
async def test_can_user_read_allowed(mock_openfga_client: AsyncMock) -> None:
    """Test can_user_read when permission is allowed."""
    mock_response = CheckResponse(allowed=True, resolution="")
    mock_openfga_client.check.return_value = mock_response

    user_id = "anne"
    document_id = "doc123"

    result = await can_user_read(mock_openfga_client, user_id, document_id)

    assert result is True
    mock_openfga_client.check.assert_awaited_once()

    # Get the actual call arguments
    called_with_request = mock_openfga_client.check.call_args[0][0]
    assert isinstance(called_with_request, ClientCheckRequest)
    assert called_with_request.user == f"user:{user_id}"
    assert called_with_request.relation == "can_read"
    assert called_with_request.object == f"item:{document_id}"


@pytest.mark.asyncio
async def test_can_user_read_not_allowed(mock_openfga_client: AsyncMock) -> None:
    """Test can_user_read when permission is not allowed."""
    mock_response = CheckResponse(allowed=False, resolution="")
    mock_openfga_client.check.return_value = mock_response

    user_id = "bob"
    document_id = "doc456"

    result = await can_user_read(mock_openfga_client, user_id, document_id)

    assert result is False
    mock_openfga_client.check.assert_awaited_once()

    called_with_request = mock_openfga_client.check.call_args[0][0]
    assert isinstance(called_with_request, ClientCheckRequest)
    assert called_with_request.user == f"user:{user_id}"
    assert called_with_request.relation == "can_read"
    assert called_with_request.object == f"item:{document_id}"


@pytest.mark.asyncio
async def test_can_user_read_custom_relation_and_object_type(
    mock_openfga_client: AsyncMock,
) -> None:
    """Test can_user_read with custom relation and object_type."""
    mock_response = CheckResponse(allowed=True, resolution="")
    mock_openfga_client.check.return_value = mock_response

    user_id = "charlie"
    document_id = "report001"
    custom_relation = "can_edit"
    custom_object_type = "document"

    result = await can_user_read(
        mock_openfga_client,
        user_id,
        document_id,
        relation=custom_relation,
        object_type=custom_object_type,
    )

    assert result is True
    mock_openfga_client.check.assert_awaited_once()

    called_with_request = mock_openfga_client.check.call_args[0][0]
    assert isinstance(called_with_request, ClientCheckRequest)
    assert called_with_request.user == f"user:{user_id}"
    assert called_with_request.relation == custom_relation
    assert called_with_request.object == f"{custom_object_type}:{document_id}"
