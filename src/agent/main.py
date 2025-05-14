"""Entrypoint."""

# TODO: Create subagents for both the retrieval and the filtering through OFGA.

import json
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi_injector import Injected, attach_injector
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService, Session
from google.genai import types
from injector import Binder, Injector, SingletonScope
from loguru import logger

from src.agent.custom_types import AgentName, AppName, CustomAgentState, Message
from src.agent.di import AgentModule
from src.configuration import ConfigurationModule
from src.project_types import SerializedConfigurationPath, ShouldResolveMissingValues

parser = ArgumentParser()
parser.add_argument(
    "--configuration",
    type=str,
    help="Path where to find the serialized (in JSON) configuration.",
)
parser.add_argument(
    "--app_name",
    type=str,
    default="test_ofga_app",
    help="Name of the app",
)
parser.add_argument(
    "--agent_name",
    type=str,
    default="test_ofga_agent",
    help="Name of the agent.",
)
args = parser.parse_args()


def _bind_flags(binder: Binder) -> None:
    configuration_path = SerializedConfigurationPath(Path(args.configuration))
    binder.bind(
        SerializedConfigurationPath, to=configuration_path, scope=SingletonScope
    )
    binder.bind(
        ShouldResolveMissingValues,
        to=ShouldResolveMissingValues.YES,
        scope=SingletonScope,
    )
    binder.bind(AppName, to=AppName(args.app_name), scope=SingletonScope)
    binder.bind(AgentName, to=AgentName(args.agent_name), scope=SingletonScope)


app = FastAPI()
inj = Injector([_bind_flags, ConfigurationModule(), AgentModule()])
attach_injector(app, inj)


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


@app.post("/message")
async def new_message(
    message: Message,
    app_name: AppName = Injected(AppName),  # noqa: B008
    session_service: BaseSessionService = Injected(BaseSessionService),  # noqa: B008
    runner: Runner = Injected(Runner),  # noqa: B008
) -> dict[str, Any]:
    """New message endpoint."""
    session = get_or_create_session(
        user_id=message.user_id,
        app_name=app_name,
        session_id=message.session_id,
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
        app_name=app_name,
        user_id=message.user_id,
        session_id=message.session_id,
        session_service=session_service,
    )
    logger.info("Final Session State:")

    logger.info(json.dumps(final_session.state, indent=2))
    logger.info("-------------------------------\n")
    return message.model_dump()


def entrypoint() -> None:
    """The actual entrypoint."""
    uvicorn.run(app, host="0.0.0.0", port=8000)  # noqa: S104
