from typing import Final

import anyio

from lockbox import _lockboxes
from lockbox._config import (
    BadConfig,
    Config,
    NoSuchLockbox,
    NoSuchSecret,
    load_config,
    to_name,
)
from lockbox._lockboxes import GetSecretsError

__all__: Final = (
    "BadConfig",
    "GetSecretsError",
    "NoSuchLockbox",
    "NoSuchSecret",
    "get_secret",
)


_config: Config | None = None
_config_lock: Final = anyio.Lock()


async def _get_config() -> Config:
    global _config
    async with _config_lock:
        if _config is None:
            _config = await load_config()
        return _config


async def get_secret(lockbox_name: str, secret_name: str) -> str:
    lockbox_name = to_name(lockbox_name)
    secret_name = to_name(secret_name)
    config = await _get_config()
    lockbox_config = config.get_lockbox_config(lockbox_name)
    return await _lockboxes.get_secret(
        config.account_id,
        lockbox_name,
        lockbox_config.service_access_token,
        lockbox_config.get_secret_reference(secret_name),
    )


async def get_secrets(lockbox_name: str, *secret_names: str) -> tuple[str, ...]:
    lockbox_name = to_name(lockbox_name)
    secret_names = tuple(to_name(secret_name) for secret_name in secret_names)
    config = await _get_config()
    lockbox_config = config.get_lockbox_config(lockbox_name)
    references = [
        lockbox_config.get_secret_reference(secret_name)
        for secret_name in secret_names
    ]
    secrets = await _lockboxes.get_secrets(
        config.account_id,
        lockbox_name,
        lockbox_config.service_access_token,
        set(references),
    )
    return tuple(secrets[reference] for reference in references)
