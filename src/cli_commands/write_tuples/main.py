"""Entrypoint for the write tuples CLI command."""

import asyncio
from argparse import ArgumentParser
from pathlib import Path

from injector import Binder, Injector, SingletonScope
from loguru import logger
from openfga_sdk import OpenFgaClient
from openfga_sdk.client.client import ClientTuple
from openfga_sdk.exceptions import ValidationException

from src.cli_commands.write_tuples.entities import TupleCollection
from src.configuration import ConfigurationModule
from src.configuration.configuration_model import (
    GeneralConfiguration,
)
from src.project_types import (
    SerializedConfigurationPath,
    ShouldResolveMissingValues,
)
from src.project_types.utils import load_json_from_file_path_as_pydantic_model


async def _main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "--configuration",
        type=str,
        required=True,
        help="Path where to find the serialized (in JSON) configuration.",
    )
    parser.add_argument(
        "--tuples_document",
        type=str,
        required=True,
        help="Path to where to find the tuples document.",
    )
    args = parser.parse_args()

    def _bind_flags(binder: Binder) -> None:
        configuration_path = SerializedConfigurationPath(Path(args.configuration))
        binder.bind(
            SerializedConfigurationPath, to=configuration_path, scope=SingletonScope
        )
        binder.bind(
            ShouldResolveMissingValues,
            to=ShouldResolveMissingValues.NO,
            scope=SingletonScope,
        )

    tuples = load_json_from_file_path_as_pydantic_model(
        args.tuples_document, model=TupleCollection
    )
    injector = Injector(modules=[_bind_flags, ConfigurationModule])
    client = injector.get(OpenFgaClient)
    config = injector.get(GeneralConfiguration)

    try:
        for store_name, tuple_list in tuples.store_to_tuples.items():
            store_configuration = config.get_store_configuration_by_store_name(
                store_name
            )
            logger.info("Inserting tuples in store {}", store_name)
            for _tuple in tuple_list:
                logger.info(
                    "Writing tuple {tuple_name} into store {store_name} ({store_id})",
                    tuple_name=_tuple.friendly_name,
                    store_name=store_configuration.store_name,
                    store_id=store_configuration.store_id,
                )
                user, relation, object = tuple(_tuple.relation_body.strip().split(" "))  # noqa: A001
                logger.debug(
                    "user: {}, relation: {}, object: {}", user, relation, object
                )
                client_tuple = ClientTuple(user=user, relation=relation, object=object)
                try:
                    await client.delete_tuples([client_tuple])
                    logger.debug("Tuple already present.")
                except Exception:  # noqa: BLE001
                    logger.debug("Tuple not already present.")
                res = await client.write_tuples(body=[client_tuple])
                if res and res.writes:
                    logger.debug("Result {}", res.writes[0].success)
                else:
                    logger.error(
                        "Res is none. Store name: {}, tuple friendly_name {}",
                        store_name,
                        _tuple.friendly_name,
                    )
                    raise RuntimeError("Res shouldn't be None")  # noqa: TRY003
    except ValidationException as e:
        logger.error("{}", e)
        logger.exception("Error inserting tuples into store.")
    finally:
        await client.close()


def entrypoint() -> None:
    """Actual entrypoint."""
    asyncio.run(_main())
