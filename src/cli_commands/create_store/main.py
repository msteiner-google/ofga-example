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
from src.ofga_operations.store import get_or_create_store
from src.project_types import (
    SerializedConfigurationPath,
    ShouldResolveMissingValues,
    ShouldSaveUpdatedConfiguration,
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

    store_configurations = GeneralConfiguration.get_store_configurations()
    config = injector.get(GeneralConfiguration)
    client = injector.get(OpenFgaClient)

    for store_configuration_dict_key in store_configurations:
        logger.debug("Creating store {}", store_configuration_dict_key)
        store_configuration: OFGAStoreConfiguration = getattr(
            config, store_configuration_dict_key
        )
        response = await get_or_create_store(store_configuration, client)
        store_id = response.id
        logger.debug(
            "Created store {} and has id {}", store_configuration_dict_key, store_id
        )
        store_configuration.store_id = store_id

    logger.info("Found the following store configurations: {}", store_configurations)
    with Path(args.save_configuration_path).open("w", encoding="utf-8") as f:
        f.write(config.model_dump_json(indent=4))
    logger.info("config: {}", config)


def entrypoint() -> None:
    """Actual entrypoint."""
    asyncio.run(_main())
