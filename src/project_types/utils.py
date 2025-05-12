"""Utilities for types."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeVar, cast

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def _load_file(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(  # noqa: TRY003
            f"Path {path_str} does not exists. Resolved path = {path.absolute()!s}"
        )
    with path.open("r") as f:
        return f.read()


def load_json_from_file_path(file_path: str) -> Mapping[str, Any]:
    """Helper function to load and parse JSON from a file path using _load_file."""
    try:
        file_content = _load_file(file_path)
        return cast("Mapping", json.loads(file_content))
    except FileNotFoundError as e:
        # Convert to ValueError for Pydantic to catch as a validation error
        raise ValueError(f"Security model file not found: {file_path}") from e  # noqa: TRY003
    except json.JSONDecodeError as e:
        raise ValueError(  # noqa: TRY003
            f"Error decoding JSON from security model file '{file_path}': "
            f"{e.msg} (at line {e.lineno} column {e.colno})"
        ) from e
    except Exception as e:  # Catch any other loading errors
        raise ValueError(  # noqa: TRY003
            f"Could not load security model from file '{file_path}': {e!s}"
        ) from e


def load_json_from_file_path_as_pydantic_model[T: BaseModel](
    file_path: str, model: type[T]
) -> T:
    """Helper function to load and parse JSON from a file path using _load_file."""
    try:
        file_content = _load_file(file_path)
        return model.model_validate_json(file_content)
    except FileNotFoundError as e:
        # Convert to ValueError for Pydantic to catch as a validation error
        raise ValueError(f"Security model file not found: {file_path}") from e  # noqa: TRY003
    except json.JSONDecodeError as e:
        raise ValueError(  # noqa: TRY003
            f"Error decoding JSON from security model file '{file_path}': "
            f"{e.msg} (at line {e.lineno} column {e.colno})"
        ) from e
    except Exception as e:  # Catch any other loading errors
        raise ValueError(  # noqa: TRY003
            f"Could not load security model from file '{file_path}': {e!s}"
        ) from e
