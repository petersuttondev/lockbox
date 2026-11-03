import importlib.metadata
import pathlib
import subprocess
from collections.abc import Iterable
from itertools import count
from typing import Final, final

import anyio
from onepassword.client import Client, DesktopAuth  # pyright: ignore[reportMissingTypeStubs]

from lockbox._config import (
    AccountID,
    Name,
    SecretReference,
    to_secret_reference,
)
from lockbox._tokens import (
    LockboxLocked,
    delete_service_account_token,
    get_service_account_token,
    set_service_account_token,
)

__all__: Final = (
    "GetSecretsError",
    "get_secret",
    "lock_lockbox",
    "unlock_lockbox",
)

_VERSION: Final = importlib.metadata.version("lockbox")


async def _authenticate(auth: str | DesktopAuth) -> Client:
    return await Client.authenticate(
        auth=auth,
        integration_name="lockbox",
        integration_version=f"v{_VERSION}",
    )


async def _try_authenticate(auth: str | DesktopAuth) -> Client | None:
    try:
        return await _authenticate(auth)
    except RuntimeError as error:
        if error.args:
            arg = error.args[0]
            if isinstance(arg, str) and arg.startswith(
                "desktop app connection channel is closed."
            ):
                return None
        raise


def _start_1password() -> None:
    subprocess.Popen(
        ("1password", "--silent"),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=pathlib.Path.home(),
        start_new_session=True,
    )


async def _make_desktop_client(account_id: AccountID) -> Client:
    auth = DesktopAuth(account_id)
    if (client := await _try_authenticate(auth)) is not None:
        return client
    _start_1password()
    with anyio.move_on_after(10):
        for attempt in count():
            await anyio.sleep(0.1 * 2**attempt)
            if (client := await _try_authenticate(auth)) is not None:
                return client
    return await _authenticate(auth)


async def unlock_lockbox(
    account_id: AccountID,
    lockbox_name: Name,
    service_account_token_reference: SecretReference,
) -> str:
    client = await _make_desktop_client(account_id)
    token = await client.secrets.resolve(service_account_token_reference)
    await set_service_account_token(lockbox_name, token)
    return token


async def lock_lockbox(lockbox: Name) -> None:
    await delete_service_account_token(lockbox)


_AUTHENTICATION_ERROR_MESSAGE: Final = "authentication error: you don't have the right permissions to access this resource"


async def _make_service_client(
    account_id: AccountID,
    lockbox_name: Name,
    service_account_token_reference: SecretReference,
) -> Client:
    try:
        token = await get_service_account_token(lockbox_name)
    except LockboxLocked:
        token = await unlock_lockbox(
            account_id, lockbox_name, service_account_token_reference
        )
    try:
        return await _authenticate(token)
    except Exception as error:
        if not error.args:
            raise
        arg = error.args[0]
        if not isinstance(arg, str) or arg != _AUTHENTICATION_ERROR_MESSAGE:
            raise
        await delete_service_account_token(lockbox_name)
        next_token = await unlock_lockbox(
            account_id, lockbox_name, service_account_token_reference
        )
        if next_token == token:
            raise
        return await _authenticate(next_token)


async def get_secret(
    account_id: AccountID,
    lockbox_name: Name,
    service_account_token_reference: SecretReference,
    secret_reference: SecretReference,
) -> str:
    client = await _make_service_client(
        account_id,
        lockbox_name,
        service_account_token_reference,
    )
    return await client.secrets.resolve(secret_reference)


@final
class GetSecretsError(Exception):
    pass


async def get_secrets(
    account_id: AccountID,
    lockbox_name: Name,
    service_account_token_reference: SecretReference,
    secret_references: Iterable[SecretReference],
) -> dict[SecretReference, str]:
    secret_reference_list: list[str] = list(secret_references)
    if not secret_reference_list:
        return {}
    client = await _make_service_client(
        account_id,
        lockbox_name,
        service_account_token_reference,
    )
    responses = await client.secrets.resolve_all(secret_reference_list)
    unseen = set(secret_reference_list)
    secrets: dict[SecretReference, str] = {}
    for secret_reference, response in responses.individual_responses.items():
        if response.error is not None:
            raise GetSecretsError(
                f"{secret_reference}: {response.error.type.value}"
            )
        assert response.content is not None
        if secret_reference not in unseen:
            raise GetSecretsError(
                f"Received response for unrequested secret with reference {secret_reference!r}."
            )
        secrets[to_secret_reference(secret_reference)] = response.content.secret
        unseen.remove(secret_reference)
    if unseen:
        raise GetSecretsError(
            f"No response for secrets with reference {', '.join(sorted(map(repr, unseen)))}."
        )
    return secrets
