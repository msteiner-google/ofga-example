"""Module containing the types used for the project."""

from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import NewType

SerializedConfigurationPathStr = NewType("SerializedConfigurationPathStr", str)
SerializedConfigurationPath = NewType("SerializedConfigurationPath", Path)
SerializedConfigurationMapping = NewType("SerializedConfigurationMapping", Mapping)

OFGAServerURL = NewType("OFGAServerURL", str)
OFGAStoreName = NewType("OFGAStoreName", str)
OFGAStoreId = NewType("OFGAStoreId", str) | None
OFGASecurityModel = NewType("OFGASecurityModel", Mapping)


class ShouldResolveMissingValues(StrEnum):
    """Whether or not should resolve missing values."""

    YES = "YES"
    NO = "NO"


class ShouldSaveUpdatedConfiguration(StrEnum):
    """Whether or not to save the updated configuration."""

    YES = "YES"
    NO = "NO"
