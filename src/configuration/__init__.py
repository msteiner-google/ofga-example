"""Configuration module."""

import asyncio
import json
from typing import TYPE_CHECKING, cast

from injector import (
    Module,
    multiprovider,
    provider,
    singleton,
)

from configuration.configuration_model import GeneralConfiguration
from ofga_operations.store import get_or_create_store
from project_types import (
    SerializedConfigurationMapping,
    SerializedConfigurationPath,
    ShouldResolveMissingValues,
)

if TYPE_CHECKING:
    from openfga_sdk.models.create_store_response import CreateStoreResponse


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
