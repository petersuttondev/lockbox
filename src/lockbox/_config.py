import os
import re
from collections.abc import Mapping
from typing import Annotated, Final, NewType, final, override

import anyio
from pydantic.config import ConfigDict
from pydantic.main import BaseModel
from pydantic.types import StringConstraints
from pydantic_core import ValidationError
from ruamel.yaml.error import YAMLError

from lockbox._util import yaml

__all__: Final = (
    "AccountID",
    "BadConfig",
    "Config",
    "LockboxConfig",
    "Name",
    "NoSuchLockbox",
    "NoSuchSecret",
    "SecretReference",
    "load_config",
    "to_account_id",
    "to_name",
    "to_secret_reference",
)


Name: Final = NewType("Name", str)

_NAME_PATTERN: Final = r"^[a-z0-9-]+$"

_match_name: Final = re.compile(_NAME_PATTERN).fullmatch


def to_name(text: str) -> Name:
    if _match_name(text) is None:
        raise ValueError(f"{text!r} does not match pattern {_NAME_PATTERN!r}")
    return Name(text)


type _Name = Annotated[Name, StringConstraints(pattern=_NAME_PATTERN)]

_SEGMENT: Final = r"[0-9A-Za-z._\x20-]+"  # \x20: space

_QUERY: Final = (
    r"\?(attribute=(type|value|title|id|purpose|otp|totp)|ssh-format=openssh)"
)
_SECRET_REFERENCE_PATTERN: Final = (
    rf"^op://{_SEGMENT}/{_SEGMENT}(/{_SEGMENT})?/{_SEGMENT}({_QUERY})?$"
)

_match_secret_reference: Final = re.compile(_SECRET_REFERENCE_PATTERN).fullmatch

SecretReference: Final = NewType("SecretReference", str)


def to_secret_reference(text: str) -> SecretReference:
    if _match_secret_reference(text) is None:
        raise ValueError(
            f"{text!r} does not match pattern {_SECRET_REFERENCE_PATTERN!r}"
        )
    return SecretReference(text)


type _SecretReference = Annotated[
    SecretReference, StringConstraints(pattern=_SECRET_REFERENCE_PATTERN)
]


@final
class NoSuchSecret(Exception):
    @override
    def __init__(self, secret_name: Name) -> None:
        super().__init__(f"No secret named {secret_name!r} configured")


@final
class LockboxConfig(BaseModel, frozen=True):
    model_config = ConfigDict(extra="forbid", strict=True)
    service_access_token: Final[_SecretReference]
    secrets: Final[Mapping[_Name, _SecretReference]]

    def get_secret_reference(self, secret_name: Name) -> SecretReference:
        try:
            return self.secrets[secret_name]
        except KeyError as error:
            raise NoSuchSecret(secret_name) from error


AccountID: Final = NewType("AccountID", str)

_ACCOUNT_ID_PATTERN: Final = "^[0-9A-Z]{26}$"

_match_account_id: Final = re.compile(_ACCOUNT_ID_PATTERN).fullmatch


def to_account_id(text: str) -> AccountID:
    if _match_account_id(text) is None:
        raise ValueError(
            f"{text!r} does not match pattern {_ACCOUNT_ID_PATTERN!r}"
        )
    return AccountID(text)


type _AccountID = Annotated[
    AccountID, StringConstraints(pattern=_ACCOUNT_ID_PATTERN)
]


@final
class NoSuchLockbox(Exception):
    @override
    def __init__(self, lockbox_name: Name) -> None:
        super().__init__(f"No lockbox named {lockbox_name!r} configured")


@final
class Config(BaseModel, frozen=True):
    model_config = ConfigDict(extra="forbid", strict=True)
    account_id: Final[_AccountID]
    lockboxes: Final[Mapping[_Name, LockboxConfig]]

    def get_lockbox_config(self, lockbox_name: Name) -> LockboxConfig:
        try:
            return self.lockboxes[lockbox_name]
        except KeyError as error:
            raise NoSuchLockbox(lockbox_name) from error


async def _get_config_home() -> anyio.Path:
    if (config_home_text := os.environ.get("XDG_CONFIG_HOME")) is not None:
        config_home = anyio.Path(config_home_text)
        if config_home.is_absolute():
            return config_home
    return (await anyio.Path.home()) / ".config"


async def _get_config_path() -> anyio.Path:
    return await _get_config_home() / "lockbox/config.yaml"


@final
class BadConfig(Exception):
    pass


async def load_config() -> Config:
    config_path = await _get_config_path()
    try:
        async with await config_path.open("r") as config_file:
            config_text = await config_file.read()
    except FileNotFoundError as error:
        raise BadConfig(
            f"Configuration missing at {os.fspath(config_path)!r}."
        ) from error
    try:
        return Config.model_validate(yaml.load(config_text))
    except (YAMLError, ValidationError) as error:
        raise BadConfig(f"{os.fspath(config_path)}: {error}") from error
