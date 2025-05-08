"""Module containing the types used for the project."""

from collections.abc import Mapping
import enum
from pathlib import Path
from typing import NewType


SerializedConfigurationPathStr = NewType("SerializedConfigurationPathStr", str)
SerializedConfigurationPath = NewType("SerializedConfigurationPath", Path)
SerializedConfigurationMapping = NewType("SerializedConfigurationMapping", Mapping)

OFGAServerURL = NewType("OFGAServerURL", str)
OFGAStoreName = NewType("OFGAStoreName", str)
OFGAStoreId = NewType("OFGAStoreId", str) | None


class ShouldResolveMissingValues(enum.Enum):
    """Whether or not should resolve missing values."""

    YES = 0
    NO = 1
