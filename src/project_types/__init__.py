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


class ACLType(StrEnum):
    """The ACL type for a given store.

    *DEFAULT_DENY* means that the the presence of a connection between subjcet and
        object signifies that the subject CAN perform the relation to the object. The
        absence means that it can not.
    *DEFAULT_ALLOW_WITH_EXPLICIT_DENY* is the opposite, subjects default to be able to
        perform the relation to the corresponing object when nothing is specified. The
        presence of a connection means they can not.
    """

    DEFAULT_DENY = "DEFAULT_DENY"
    DEFAULT_ALLOW_WITH_EXPLICIT_DENY = "DEFAULT_ALLOW_WITH_EXPLICIT_DENY"
