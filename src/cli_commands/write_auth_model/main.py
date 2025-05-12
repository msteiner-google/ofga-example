"""Main for creating a store."""

import asyncio
from argparse import ArgumentParser
from pathlib import Path

from injector import Binder, Injector, SingletonScope
from loguru import logger

from src.configuration import ConfigurationModule
from src.configuration.configuration_model import GeneralConfiguration
from src.ofga_operations.store import write_authorization_id
from src.project_types import (
    OFGASecurityModel,
    SerializedConfigurationPath,
    ShouldResolveMissingValues,
    ShouldSaveUpdatedConfiguration,
)


def _main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "--configuration",
        type=str,
        default=None,
        help="Path where to find the serialized (in JSON) configuration.",
    )
    parser.add_argument(
        "--save_updated_configuration",
        type=ShouldSaveUpdatedConfiguration,
        choices=list(ShouldSaveUpdatedConfiguration),
        required=False,
        default="YES",
        help="Specify whether to save the updated configuration.",
    )
    parser.add_argument(
        "--save_configuration_path",
        type=str,
        default="updated_configuration.json",
        help="Path where to find the serialized (in JSON) configuration.",
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

    injector = Injector(modules=[_bind_flags, ConfigurationModule])

    config = injector.get(GeneralConfiguration)
    auth_model = injector.get(OFGASecurityModel)
    write_auth_response = asyncio.run(write_authorization_id(config, auth_model))
    config.store_configuration.authorization_model_id = (
        write_auth_response.authorization_model_id
    )
    if args.save_updated_configuration == ShouldSaveUpdatedConfiguration.YES:
        with Path(args.save_configuration_path).open("w", encoding="utf-8") as f:
            f.write(config.model_dump_json(indent=4))
    logger.info("config: {}", config)


def entrypoint() -> None:
    """Actual entrypoint."""
    _main()
