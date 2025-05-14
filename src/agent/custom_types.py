"""Custom types for the agent."""

from google.genai import types
from typing import NewType
from pydantic import BaseModel, Field
from uuid_extensions import uuid7str


class Message(BaseModel):
    """Base message class."""

    body: str = Field()
    user_id: str = Field()
    session_id: str = Field(default_factory=uuid7str)


class CustomAgentState(BaseModel):
    """Custom state for the agent."""

    user_visible_messages: list[types.Content] = Field(default=[])
    all_messages: list[types.Content] = Field(default=[])


AppName = NewType("AppName", str)
AgentName = NewType("AgentName", str)
