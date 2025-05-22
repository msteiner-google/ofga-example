"""Defines the configuration model."""

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
