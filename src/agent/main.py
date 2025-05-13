"""Entrypoint."""

import json
from collections.abc import AsyncGenerator
from typing import Any, override

import uvicorn
from fastapi import FastAPI
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService, InMemorySessionService, Session
from google.genai import types
from loguru import logger

from src.agent.custom_types import CustomAgentState, Message

app = FastAPI()


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


APP_NAME = "test_ofga"
SESSION_ID = "test-session-id"
USER_ID = "test-user"
agent = OFGATestAgent(name=f"{APP_NAME}_agent")
session_service = InMemorySessionService()


def get_or_create_session(
    user_id: str, session_id: str, app_name: str, session_service: BaseSessionService
) -> Session:
    """Get's or create a session."""
    maybe_session = session_service.get_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
    if maybe_session:
        logger.info("returning existing session.")
        return maybe_session
    logger.info("Creating new session.")
    return session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=CustomAgentState().model_dump(),
    )


runner = Runner(
    agent=agent,  # Pass the custom orchestrator agent
    app_name=APP_NAME,
    session_service=session_service,
)


@app.post("/message")
async def new_message(message: Message) -> dict[str, Any]:
    """New message endpoint."""
    session = get_or_create_session(
        user_id=USER_ID,
        app_name=APP_NAME,
        session_id=SESSION_ID,
        session_service=session_service,
    )
    content = types.Content(role="user", parts=[types.Part(text=message.body)])
    events = runner.run_async(
        user_id=session.user_id, session_id=session.id, new_message=content
    )
    final_response = "No final response captured."
    async for event in events:
        if event.is_final_response() and event.content and event.content.parts:
            final_response = event.content.parts[0].text

    logger.info("--- Agent Interaction Result ---")
    logger.info("Agent Final Response: {}", final_response)

    final_session = get_or_create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        session_service=session_service,
    )
    logger.info("Final Session State:")

    logger.info(json.dumps(final_session.state, indent=2))
    logger.info("-------------------------------\n")
    return message.model_dump()


def entrypoint() -> None:
    """The actual entrypoint."""
    uvicorn.run(app, host="0.0.0.0", port=8080)  # noqa: S104
