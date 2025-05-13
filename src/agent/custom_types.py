"""Custom types for the agent."""

from google.genai import types
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Base message class."""

    body: str = Field()


class CustomAgentState(BaseModel):
    """Custom state for the agent."""

    user_visible_messages: list[types.Content] = Field(default=[])
    all_messages: list[types.Content] = Field(default=[])
