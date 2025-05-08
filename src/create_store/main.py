"""Main for creating a store."""

from argparse import ArgumentParser
from pathlib import Path

from injector import Binder, Injector, SingletonScope
from loguru import logger

from configuration import ConfigurationModule
from configuration.configuration_model import GeneralConfiguration
from project_types import SerializedConfigurationPath, ShouldResolveMissingValues


def _main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "--configuration",
        type=str,
        default=None,
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
    logger.info("config: {}", config)


def entrypoint() -> None:
    """Actual entrypoint."""
    _main()
