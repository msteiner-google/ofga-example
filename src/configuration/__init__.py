"""Configuration module."""

import json
from typing import TYPE_CHECKING, cast

from injector import (
    Module,
    multiprovider,
    provider,
    singleton,
)
from openfga_sdk import (
    OpenFgaClient,
)
from pydantic import ValidationError

from src.configuration.configuration_model import (
    GeneralConfiguration,
    OFGAServerConfiguration,
    OFGAStoreConfiguration,
)
from src.ofga_operations.store import get_or_create_store
from src.ofga_operations.utils import get_client
from src.project_types import (
    OFGASecurityModel,
    SerializedConfigurationMapping,
    SerializedConfigurationPath,
    ShouldResolveMissingValues,
)
from src.project_types.utils import load_json_from_file_path

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
        if not model.store_for_documents_configuration.store_id:
            response = cast(
                "CreateStoreResponse",
                get_or_create_store(model),
            )
            model.store_for_documents_configuration.store_id = response.id

        return model

    @singleton
    @provider
    def _provide_store_configuration(  # noqa: PLR6301
        self, general_configuration: GeneralConfiguration
    ) -> OFGAStoreConfiguration:
        return general_configuration.store_for_documents_configuration

    @singleton
    @provider
    def _provide_server_configuration(  # noqa: PLR6301
        self, general_configuration: GeneralConfiguration
    ) -> OFGAServerConfiguration:
        return general_configuration.server_configuration

    @provider
    def _provide_ofga_api_client(  # noqa: PLR6301
        self,
        config: GeneralConfiguration,
    ) -> OpenFgaClient:
        return get_client(config)

    @singleton
    @provider
    def _provide_authorization_model(  # noqa: PLR6301
        self, configuration: OFGAStoreConfiguration
    ) -> OFGASecurityModel:
        if configuration.authorization_model_file is None:
            raise ValidationError("Authorization model was not provided.")  # noqa: TRY003
        mapping = load_json_from_file_path(configuration.authorization_model_file)
        return OFGASecurityModel(mapping)
