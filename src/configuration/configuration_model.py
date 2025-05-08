"""Defines the configuration model."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


def _load_file(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        raise ValueError(  # noqa: TRY003
            f"Path {path_str} does not exists. Resolved path = {path.absolute()!s}"
        )
    with path.open("r") as f:
        return f.read()


class OpenFGAServerConfiguration(BaseModel):
    """Configuration class."""

    api_url: str = Field(default="http://34.79.138.32:8080")


class StoreConfiguration(BaseModel):
    """Configuration for stores."""

    store_name: str = Field(
        description="The store mnemonic name you want to give.", default="default_store"
    )
    store_id: str | None = Field(
        default=None,
        description="The store id, if known. If not known we'll try to resolve it.",
    )
    security_model: Mapping[str, Any] = Field(
        description="The security model to use for this store.",
        default_factory=lambda: json.loads(_load_file("authorization_model.json")),
    )
