"""Configuration module."""

import json
from typing import cast

from injector import (
    Module,
    multiprovider,
    provider,
    singleton,
)
from loguru import logger
from openfga_sdk import (
    OpenFgaClient,
)
from pydantic import ValidationError

from src.configuration.configuration_model import (
    GeneralConfiguration,
    OFGAServerConfiguration,
    OFGAStoreConfiguration,
)
from src.ofga_operations.utils import get_client
from src.project_types import (
    OFGASecurityModel,
    SerializedConfigurationMapping,
    SerializedConfigurationPath,
)
from src.project_types.utils import load_json_from_file_path


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
    ) -> GeneralConfiguration:
        return cast(
            "GeneralConfiguration", GeneralConfiguration.model_validate(mapping)
        )

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

    @singleton
    @provider
    def _provide_ofga_api_client(  # noqa: PLR6301
        self,
        config: GeneralConfiguration,
    ) -> OpenFgaClient:
        logger.warning("Getting a generic client, i.e. not specialized for a store.")
        return get_client(config, maybe_store_conf=None)

    @singleton
    @multiprovider
    def _provide_ofga_api_clients_for_each_store(  # noqa: PLR6301
        self,
        config: GeneralConfiguration,
    ) -> dict[str, OpenFgaClient]:
        store_keys = GeneralConfiguration.get_store_configurations()
        return {key: get_client(config, getattr(config, key)) for key in store_keys}

    @singleton
    @multiprovider
    def _provide_authorization_model(  # noqa: PLR6301
        self, configuration: GeneralConfiguration
    ) -> dict[str, OFGASecurityModel]:
        store_configurations = GeneralConfiguration.get_store_configurations()
        result = {}
        for store_configuration_dict_key in store_configurations:
            store_configuration: OFGAStoreConfiguration = getattr(
                configuration, store_configuration_dict_key
            )
            if store_configuration.authorization_model_file is None:
                raise ValidationError("Authorization model was not provided.")  # noqa: TRY003
            mapping = load_json_from_file_path(
                store_configuration.authorization_model_file
            )
            result[store_configuration_dict_key] = OFGASecurityModel(mapping)
        return result
