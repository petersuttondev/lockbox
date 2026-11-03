import json
import sys

import anyio
from suppress_unhandled import suppress_unhandled

from lockbox._cli import GetArgs, LockArgs, SchemaArgs, UnlockArgs, parse_args
from lockbox._config import (
    BadConfig,
    Config,
    NoSuchLockbox,
    NoSuchSecret,
    load_config,
)
from lockbox._lockboxes import get_secret, lock_lockbox, unlock_lockbox
from lockbox._util import to_system_exit


async def _load_config() -> Config:
    with to_system_exit(BadConfig):
        return await load_config()


async def _do_get(args: GetArgs) -> None:
    config = await _load_config()
    with to_system_exit(NoSuchLockbox):
        lockbox_conf = config.get_lockbox_config(args.lockbox_name)
    with to_system_exit(NoSuchSecret):
        secret_reference = lockbox_conf.get_secret_reference(args.secret_name)
    secret = await get_secret(
        config.account_id,
        args.lockbox_name,
        lockbox_conf.service_access_token,
        secret_reference,
    )
    print(secret)


async def _do_lock(args: LockArgs) -> None:
    config = await _load_config()
    with to_system_exit(NoSuchLockbox):
        config.get_lockbox_config(args.lockbox_name)
    await lock_lockbox(args.lockbox_name)


def _do_schema_sync() -> None:
    json.dump(Config.model_json_schema(), sys.stdout, indent=2)


async def _do_schema() -> None:
    await anyio.to_thread.run_sync(_do_schema_sync)


async def _do_unlock(args: UnlockArgs) -> None:
    config = await _load_config()
    with to_system_exit(NoSuchLockbox):
        lockbox_config = config.get_lockbox_config(args.lockbox_name)
    await unlock_lockbox(
        config.account_id,
        args.lockbox_name,
        lockbox_config.service_access_token,
    )


async def _async_main() -> None:
    match parse_args():
        case GetArgs() as args:
            await _do_get(args)
        case LockArgs() as args:
            await _do_lock(args)
        case SchemaArgs():
            await _do_schema()
        case UnlockArgs() as args:
            await _do_unlock(args)


def main() -> None:
    suppress_unhandled(KeyboardInterrupt, inspect_groups=True)
    anyio.run(_async_main)


if __name__ == "__main__":
    main()
