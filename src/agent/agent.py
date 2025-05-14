"""Actual agent implementation."""

from collections.abc import AsyncGenerator
from typing import override

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types
from loguru import logger


class OFGATestAgent(BaseAgent):
    """Custom agent."""

    def __init__(self, name: str) -> None:
        """Init method."""
        super().__init__(name=name)

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        for event in ctx.session.events:
            logger.info("{}", event)

        reply = types.Content(role="agent", parts=[types.Part(text="Canned response")])
        state_change = {
            "user_visible_messages": ctx.session.state["user_visible_messages"]
            + ["test"]
        }
        actions_with_update = EventActions(state_delta=state_change)
        system_event = Event(
            invocation_id="test_update", author="system", actions=actions_with_update
        )
        ctx.session_service.append_event(ctx.session, system_event)

        logger.info(ctx.session.state)
        yield Event(author="agent", content=reply)
