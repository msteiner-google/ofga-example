"""Custom types for the agent."""

from typing import NewType

from google.adk.agents import LlmAgent
from google.genai import types
from pydantic import BaseModel, Field
from uuid_extensions import uuid7str
from sqlite3 import Connection


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
DocumentListArtifactKey = NewType("DocumentListArtifactKey", str)
RowListArtifactKey = NewType("RowListArtifactKey", str)
RetrieveContextKey = NewType("RetrieveContextKey", str)
GeminiModel = NewType("GeminiModel", str)
AnsweringAgent = NewType("AnsweringAgent", LlmAgent)  # type: ignore


# Differentiate the tabular datasources by giving them their own type alias
HRDataConnection = NewType("HRDataConnection", Connection)
FinancialDataConnection = NewType("FinancialDataConnection", Connection)
