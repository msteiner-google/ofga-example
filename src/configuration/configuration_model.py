"""Defines the configuration model."""

from pydantic import BaseModel, Field


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


class GeneralConfiguration(BaseModel):
    """Root configuration."""

    server_configuration: OFGAServerConfiguration
    store_configuration: OFGAStoreConfiguration
