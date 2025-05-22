"""Defines the configuration model."""

import inspect
from typing import Self

from loguru import logger
from pydantic import BaseModel, Field

from src.project_types import ACLType


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
    authorization_model_file: str | None = Field(
        default=None,
        description="The JSON file where to find the security model definition. "
        "If provided, 'security_model' will be loaded from this file.",
    )
    authorization_model_id: str | None = Field(
        default=None,
        description="Id for the provided authorization model. This is obtained from "
        "from the server by calling the "
        "https://openfga.dev/api/service#/Authorization%20Models/WriteAuthorizationModel"
        " endpoint.",
    )
    acl_type: ACLType = Field(
        description=(
            "Which kind of ACL type this store uses. "
            "Admissible values are: DEFAULT_DENY and "
            "DEFAULT_ALLOW_WITH_EXPLICIT_DENY. "
            "More information on the type definition itself."
        )
    )


class GeneralConfiguration(BaseModel):
    """Root configuration."""

    # Server configuration.
    server_configuration: OFGAServerConfiguration

    # Here we create a store configuration for each data source.
    # Ideally there should be a 1:1 mapping, however the definition of datasource
    # can be a bit fuzzy.
    # For instance, a datasource can be either a single table/view, a dataset, or all
    # the datasets / tables under a project.
    # I see it as being a collection of data that has similar properties and having
    # the same access rules.
    store_for_documents_configuration: OFGAStoreConfiguration
    store_for_tables_with_default_deny: OFGAStoreConfiguration
    store_for_tables_with_default_allow: OFGAStoreConfiguration

    @staticmethod
    def get_store_configurations() -> list[str]:
        """Retrieves field names that are store configurations."""
        model_cls = GeneralConfiguration
        target_type = OFGAStoreConfiguration
        found_fields = []

        for field_name, field_info in model_cls.model_fields.items():
            field_annotation = field_info.annotation

            if inspect.isclass(field_annotation) and inspect.isclass(target_type):
                try:
                    if issubclass(field_annotation, target_type):
                        found_fields.append(field_name)
                        continue
                except TypeError:
                    # issubclass can raise TypeError if args
                    # are not classes (e.g. typing constructs)
                    pass

        return found_fields

    def get_store_key_by_name(self, store_name: str) -> str:
        """Given a store name retrieve the dictionary key used."""
        available_stores = GeneralConfiguration.get_store_configurations()
        for store_dict_key in available_stores:
            store: OFGAStoreConfiguration = getattr(self, store_dict_key)
            if store.store_name == store_name:
                return store_dict_key
        raise RuntimeError("Store key not found")  # noqa: TRY003

    def get_store_configuration_by_store_name(
        self, store_name: str
    ) -> OFGAStoreConfiguration:
        """Retrieves the store configuration whose name match the provided one."""
        logger.debug("Looking for store {}", store_name)
        available_store_keys: list[str] = (
            GeneralConfiguration.get_store_configurations()
        )
        for store_dict_key in available_store_keys:
            store: OFGAStoreConfiguration = getattr(self, store_dict_key)
            if store.store_name == store_name:
                return store
        raise RuntimeError("Couldn't find any store with the given name.")  # noqa: TRY003
