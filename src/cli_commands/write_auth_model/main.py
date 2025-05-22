"""Main for creating a store."""

import asyncio
from argparse import ArgumentParser
from pathlib import Path

from injector import Binder, Injector, SingletonScope
from loguru import logger
from openfga_sdk import OpenFgaClient

from src.configuration import ConfigurationModule
from src.configuration.configuration_model import (
    GeneralConfiguration,
    OFGAStoreConfiguration,
)
from src.ofga_operations.store import write_authorization_id
from src.project_types import (
    OFGASecurityModel,
    SerializedConfigurationPath,
    ShouldResolveMissingValues,
)


async def _main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "--configuration",
        type=str,
        default=None,
        help="Path where to find the serialized (in JSON) configuration.",
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
    client = injector.get(OpenFgaClient)

    store_to_auth_model = injector.get(dict[str, OFGASecurityModel])
    for dict_key, auth_model in store_to_auth_model.items():
        store_config: OFGAStoreConfiguration = getattr(config, dict_key)
        write_auth_response = await write_authorization_id(auth_model, client)
        store_config.authorization_model_id = write_auth_response.authorization_model_id

    with Path(args.save_configuration_path).open("w", encoding="utf-8") as f:
        f.write(config.model_dump_json(indent=4))
    logger.info("config: {}", config)


def entrypoint() -> None:
    """Actual entrypoint."""
    asyncio.run(_main())
