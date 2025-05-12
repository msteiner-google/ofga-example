"""Configuration module."""

import asyncio
import json
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from injector import (
    Module,
    multiprovider,
    provider,
    singleton,
)
from openfga_sdk import ClientConfiguration, OpenFgaClient
from pydantic import ValidationError
from pydantic_core.core_schema import ValidationFunction

from src.configuration.configuration_model import (
    GeneralConfiguration,
    OFGAServerConfiguration,
    OFGAStoreConfiguration,
)
from src.ofga_operations.store import get_or_create_store
from src.project_types import (
    OFGASecurityModel,
    SerializedConfigurationMapping,
    SerializedConfigurationPath,
    ShouldResolveMissingValues,
)

if TYPE_CHECKING:
    from openfga_sdk.models.create_store_response import CreateStoreResponse


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


class ConfigurationModule(Module):
    """Module that provides the configuration."""

    @singleton
    @multiprovider
    def _provide_deserialized_configuration(  # noqa: PLR6301
        self,
        path: SerializedConfigurationPath,
    ) -> SerializedConfigurationMapping:
        if not path.exists():
            raise ValueError(  # noqa: TRY003
                f"provided path doesn't exist. Resolved path: {path.absolute()!s} ."
            )
        if path.is_dir():
            raise ValueError(  # noqa: TRY003
                "Provided path to serialized configuration is a directory."
            )
        with path.open("r") as f:
            return SerializedConfigurationMapping(json.loads(f.read()))

    @singleton
    @provider
    def _provide_general_configuration(  # noqa: PLR6301
        self,
        mapping: SerializedConfigurationMapping,
        should_resolve_missing_values: ShouldResolveMissingValues,
    ) -> GeneralConfiguration:
        model: GeneralConfiguration = GeneralConfiguration.model_validate(mapping)
        if should_resolve_missing_values == ShouldResolveMissingValues.NO:
            return model
        if not model.store_configuration.store_id:
            response = cast(
                "CreateStoreResponse", asyncio.run(get_or_create_store(model))
            )
            model.store_configuration.store_id = response.id

        return model

    @singleton
    @provider
    def _provide_store_configuration(  # noqa: PLR6301
        self, general_configuration: GeneralConfiguration
    ) -> OFGAStoreConfiguration:
        return general_configuration.store_configuration

    @singleton
    @provider
    def _provide_server_configuration(  # noqa: PLR6301
        self, general_configuration: GeneralConfiguration
    ) -> OFGAServerConfiguration:
        return general_configuration.server_configuration

    @provider
    def _provide_ofga_api_client(
        self,
        server_configuration: OFGAServerConfiguration,
        store_configuration: OFGAStoreConfiguration,
    ) -> OpenFgaClient:
        client_configuration = ClientConfiguration(
            api_url=server_configuration.api_url,
            store_id=store_configuration.store_id,
            authorization_model_id=store_configuration.authorization_model_id,
        )
        return OpenFgaClient(client_configuration)

    @singleton
    @provider
    def _provide_authorization_model(  # noqa: PLR6301
        self, configuration: OFGAStoreConfiguration
    ) -> OFGASecurityModel:
        if configuration.authorization_model_file is None:
            raise ValidationError("Authorization model was not provided.")  # noqa: TRY003
        mapping = load_json_from_file_path(configuration.authorization_model_file)
        return OFGASecurityModel(mapping)
