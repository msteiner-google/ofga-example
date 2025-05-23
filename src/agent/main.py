"""Entrypoint."""

from argparse import ArgumentParser
from contextlib import asynccontextmanager
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
from openfga_sdk import OpenFgaClient

from src.agent.custom_types import (
    AgentName,
    AppName,
    GeminiModel,
    Message,
)
from src.agent.di import AgentModule
from src.agent.sub_agents.di import SubAgentModule
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
parser.add_argument(
    "--model_version",
    type=str,
    default="gemini-2.0-flash-001",
    help="Gemini version to use.",
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
    binder.bind(GeminiModel, to=GeminiModel(args.model_version), scope=SingletonScope)
    binder.bind(AppName, to=AppName(args.app_name), scope=SingletonScope)
    binder.bind(AgentName, to=AgentName(args.agent_name), scope=SingletonScope)


inj = Injector([
    # Bind flags so that they are available by the other modules.
    _bind_flags,
    # Confiugration module
    ConfigurationModule(),
    # Module for the sub agents
    SubAgentModule(),
    # Main agent module.
    AgentModule(),
])


@asynccontextmanager
async def lifespan(_: FastAPI):  # noqa: ANN201, D103
    # Startup ops.
    yield
    clients = inj.get(dict[str, OpenFgaClient])
    for client in clients.values():
        logger.info("Closing pending open fga clients.")
        await client.close()


app = FastAPI(lifespan=lifespan)
attach_injector(app, inj)


async def get_or_create_session(
    user_id: str,
    session_id: str,
    app_name: str,
    session_service: BaseSessionService,
    user_content: types.Content | None = None,
) -> Session:
    """Get's or create a session."""
    maybe_session = await session_service.get_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
    if maybe_session:
        logger.info("returning existing session.")
        return maybe_session
    logger.info("Creating new session.")
    return await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state={
            "last_question": user_content.parts[0].text
            if user_content and user_content.parts and user_content.parts[0].text
            else "",
            "previous_conversation": [],
        },
    )


@app.post("/message")
async def new_message(
    message: Message,
    app_name: AppName = Injected(AppName),  # noqa: B008
    session_service: BaseSessionService = Injected(BaseSessionService),  # noqa: B008
    runner: Runner = Injected(Runner),  # noqa: B008
) -> dict[str, Any]:
    """New message endpoint."""
    logger.info("Received new message from user {}", message.user_id)
    content = types.Content(role="user", parts=[types.Part(text=message.body)])
    session = await get_or_create_session(
        user_id=message.user_id,
        app_name=app_name,
        session_id=message.session_id,
        session_service=session_service,
        user_content=content,
    )
    events = runner.run_async(
        user_id=session.user_id, session_id=session.id, new_message=content
    )
    final_response = "No final response captured."
    async for event in events:
        if (
            event
            and event.is_final_response()
            and event.content
            and event.content.parts
            and event.content.parts[0].text
        ):
            final_response = event.content.parts[0].text

    return {"answer": final_response}


def entrypoint() -> None:
    """The actual entrypoint."""
    uvicorn.run(app, host="0.0.0.0", port=8000)  # noqa: S104
