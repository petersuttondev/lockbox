from collections.abc import Generator
from contextlib import contextmanager
from typing import Final

from ruamel.yaml.main import YAML

__all__: Final = (
    "to_system_exit",
    "yaml",
)

yaml: Final = YAML(typ="safe")


@contextmanager
def to_system_exit(*exceptions: type[BaseException]) -> Generator[None]:
    try:
        yield
    except BaseException as error:
        if isinstance(error, exceptions):
            raise SystemExit(str(error)) from error
        raise
