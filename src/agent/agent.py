"""Actual agent implementation."""

from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from injector import inject
from pydantic import ConfigDict

from src.agent.custom_types import (
    AgentName,
    AnsweringAgent,
    DispatcherAgent,
)


class OFGATestAgent(BaseAgent):
    """Custom agent."""

    model_config = ConfigDict(extra="allow")

    @inject
    def __init__(
        self,
        name: AgentName,
        dispatcher_agent: DispatcherAgent,
        answering_agent: AnsweringAgent,
    ) -> None:
        """Init method."""
        super().__init__(
            name=name,
        )
        self._answering_agent = answering_agent
        self._dispatcher_agent = dispatcher_agent

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        async for event in self._dispatcher_agent.run_async(ctx):
            yield event
        async for event in self._answering_agent.run_async(ctx):
            yield event
