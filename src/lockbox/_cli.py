from argparse import ArgumentParser, ArgumentTypeError
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Annotated,
    Final,
    Literal,
    LiteralString,
    final,
)

from pydantic import AfterValidator
from pydantic.config import ConfigDict
from pydantic.fields import Field
from pydantic.main import BaseModel
from pydantic.type_adapter import TypeAdapter

from lockbox._config import Name, to_name

if TYPE_CHECKING:
    from argparse import _SubParsersAction  # pyright: ignore[reportPrivateUsage]

__all__: Final = (
    "Args",
    "GetArgs",
    "LockArgs",
    "SchemaArgs",
    "UnlockArgs",
    "make_parser",
    "parse_args",
)


type _Subparsers = _SubParsersAction[ArgumentParser]

type NameField = Annotated[Name, AfterValidator(to_name)]


def _add_parser(
    subparsers: _Subparsers, subcommand: LiteralString, help: str
) -> ArgumentParser:
    parser = subparsers.add_parser(subcommand, help=help, description=help)
    parser.set_defaults(subcommand=subcommand)
    return parser


def _parse_name(value: str) -> Name:
    try:
        return to_name(value)
    except ValueError as error:
        raise ArgumentTypeError(str(error)) from error


# -- Get --------------------------------------------------------------------- #


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class GetArgs:
    lockbox_name: Final[Name]
    secret_name: Final[Name]


@final
class _GetModel(BaseModel, frozen=True):
    model_config = ConfigDict(extra="forbid", strict=True)
    subcommand: Final[Literal["get"]]  # noqa: PYI064
    lockbox_name: Final[NameField]
    secret_name: Final[NameField]


def _add_get_parser(subparsers: _Subparsers) -> None:
    help = "get a secret from a lockbox"
    parser = _add_parser(subparsers, "get", help)
    parser.add_argument("lockbox_name", type=_parse_name, metavar="lockbox")
    parser.add_argument("secret_name", type=_parse_name, metavar="secret")


def _make_get_args(model: _GetModel) -> GetArgs:
    return GetArgs(
        lockbox_name=model.lockbox_name, secret_name=model.secret_name
    )


# -- Lock -------------------------------------------------------------------- #


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class LockArgs:
    lockbox_name: Final[Name]


@final
class _LockModel(BaseModel, frozen=True):
    model_config = ConfigDict(extra="forbid", strict=True)
    subcommand: Final[Literal["lock"]]  # noqa: PYI064
    lockbox_name: Final[NameField]


def _add_lock_parser(subparsers: _Subparsers) -> None:
    help = "lock a lockbox"
    parser = _add_parser(subparsers, "lock", help)
    parser.add_argument("lockbox_name", type=_parse_name, metavar="lockbox")


def _make_lock_args(model: _LockModel) -> LockArgs:
    return LockArgs(lockbox_name=model.lockbox_name)


# -- Schema ------------------------------------------------------------------ #


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class SchemaArgs:
    pass


@final
class _SchemaModel(BaseModel, frozen=True):
    model_config = ConfigDict(extra="forbid", strict=True)
    subcommand: Final[Literal["schema"]]  # noqa: PYI064


def _add_schema_parser(subparsers: _Subparsers) -> None:
    help = "print the configuration json schema"
    _add_parser(subparsers, "schema", help)


def _make_schema_args() -> SchemaArgs:
    return SchemaArgs()


# -- Unlock ------------------------------------------------------------------ #


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class UnlockArgs:
    lockbox_name: Final[Name]


@final
class _UnlockModel(BaseModel, frozen=True):
    model_config = ConfigDict(extra="forbid", strict=True)
    subcommand: Final[Literal["unlock"]]  # noqa: PYI064
    lockbox_name: Final[NameField]


def _add_unlock_parser(subparsers: _Subparsers) -> None:
    help = "allow tools access to a lockbox's secrets"
    parser = _add_parser(subparsers, "unlock", help)
    parser.add_argument(
        "lockbox_name", type=_parse_name, help="lockbox name", metavar="lockbox"
    )


def _make_unlock_args(model: _UnlockModel) -> UnlockArgs:
    return UnlockArgs(lockbox_name=model.lockbox_name)


# ---------------------------------------------------------------------------- #

type Args = GetArgs | LockArgs | SchemaArgs | UnlockArgs

type _Model = _GetModel | _LockModel | _SchemaModel | _UnlockModel

_model_adapter: Final = TypeAdapter[_Model](
    Annotated[_Model, Field(discriminator="subcommand")]
)


def make_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="lockbox")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    _add_unlock_parser(subparsers)
    _add_lock_parser(subparsers)
    _add_get_parser(subparsers)
    _add_schema_parser(subparsers)
    return parser


def parse_args() -> Args:
    parser = make_parser()
    model = _model_adapter.validate_python(vars(parser.parse_args()))
    match model:
        case _GetModel():
            return _make_get_args(model)
        case _LockModel():
            return _make_lock_args(model)
        case _SchemaModel():
            return _make_schema_args()
        case _UnlockModel():
            return _make_unlock_args(model)
