import os
import tempfile
from typing import Final, final, override

import anyio

from lockbox._config import Name

__all__: Final = (
    "LockboxLocked",
    "delete_service_account_token",
    "get_service_account_token",
    "set_service_account_token",
)


@final
class LockboxLocked(Exception):
    @override
    def __init__(self, lockbox_name: Name) -> None:
        super().__init__(f"lockbox {lockbox_name!r} is locked")


def _get_token_path(lockbox_name: Name) -> anyio.Path:
    try:
        value = os.environ["XDG_RUNTIME_DIR"]
    except KeyError as error:
        raise RuntimeError("XDG_RUNTIME_DIR is not set") from error
    if not os.path.isabs(value):
        raise RuntimeError("XDG_RUNTIME_DIR is not absolute")
    return anyio.Path(value, "lockbox", lockbox_name)


async def get_service_account_token(lockbox_name: Name) -> str:
    token_path = _get_token_path(lockbox_name)
    try:
        return (await token_path.read_text()).strip()
    except FileNotFoundError as error:
        raise LockboxLocked(lockbox_name) from error


def _write_token(path: anyio.Path, token: bytes) -> None:
    with tempfile.NamedTemporaryFile(
        dir=path.parent, delete_on_close=False
    ) as file:
        file.write(token)
        file.close()
        os.rename(file.name, path)


async def set_service_account_token(
    lockbox_name: Name, service_access_token: str
) -> None:
    token_data = service_access_token.encode()
    token_path = _get_token_path(lockbox_name)
    await token_path.parent.mkdir(mode=0o700, exist_ok=True)
    await anyio.to_thread.run_sync(_write_token, token_path, token_data)


async def delete_service_account_token(lockbox_name: Name) -> None:
    await _get_token_path(lockbox_name).unlink(missing_ok=True)
