"""Defines the configuration model."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, Field, model_validator


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


class OFGAServerConfiguration(BaseModel):
    """Configuration class."""

    api_url: str = Field()


class OFGAStoreConfiguration(BaseModel):
    """Configuration for stores."""

    store_name: str = Field(
        description="The store mnemonic name you want to give.",
    )
    store_id: str | None = Field(
        default=None,
        description="The store id, if known. If not known we'll try to resolve it.",
    )
    security_model: Mapping[str, Any] | None = Field(
        default=None,  # Crucial: set to None, validator handles population/validation
        description="The security model to use for this store. "
        "Provide this directly or use 'security_model_file'.",
    )
    security_model_file: str | None = Field(
        default=None,  # Crucial: set to None
        description="The JSON file where to find the security model definition. "
        "If provided, 'security_model' will be loaded from this file.",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_security_model_source(cls, data: Any) -> Any:  # noqa: ANN401
        """Custom validation."""
        if not isinstance(data, dict):
            # This validator expects dictionary input, typical for model instantiation.
            # Pass through if it's not a dict, or raise an error if this
            # scenario is unexpected.
            return data

        security_model_value = data.get("security_model")
        security_model_file_value = data.get("security_model_file")

        sm_provided = security_model_value is not None
        smf_provided = security_model_file_value is not None

        if sm_provided and smf_provided:
            raise ValueError(  # noqa: TRY003
                "Provide either 'security_model' directly or "
                "'security_model_file', not both."
            )

        if not sm_provided and not smf_provided:
            raise ValueError(  # noqa: TRY003
                "Either 'security_model' or 'security_model_file' must be provided."
            )

        if smf_provided:
            # The security_model_file is provided, so load it into security_model.
            # The original security_model should not have been provided
            # (ensured by the check above).
            if not isinstance(security_model_file_value, str):
                # This should typically be caught by Pydantic's own type
                # validation for the field, but an early check can be useful.
                raise ValueError("'security_model_file' must be a string (file path).")  # noqa: TRY003

            # The load_json_from_file_path function will raise ValueError on issues,
            # which Pydantic will handle as a validation error.
            loaded_model = load_json_from_file_path(security_model_file_value)
            data["security_model"] = loaded_model
            # Optionally, you might want to remove or nullify
            # 'security_model_file' in 'data'
            # if it's considered fully processed,
            # e.g., data['security_model_file'] = None
            # However, keeping it can be useful for auditing the source.

        # If only sm_provided, data["security_model"] already has the value.
        # Pydantic will proceed to validate its type (Mapping[str, Any]).

        return data


class GeneralConfiguration(BaseModel):
    """Root configuration."""

    server_configuration: OFGAServerConfiguration
    store_configuration: OFGAStoreConfiguration
