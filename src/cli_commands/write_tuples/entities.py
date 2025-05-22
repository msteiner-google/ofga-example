"""Definition of tuples so that we can serialize/deserialize them."""

from pydantic import BaseModel, Field


class Tuple(BaseModel):
    """Definition of a single tuple."""

    friendly_name: str = Field(
        description="Friendly name used for logging/debug purposes."
    )
    relation_body: str = Field(
        description="Actual body containing the 'rule' defined by this tuple."
    )


class TupleCollection(BaseModel):
    """Definition of a collection of tuples."""

    store_to_tuples: dict[str, list[Tuple]] = Field(description="Collection of tuples.")
