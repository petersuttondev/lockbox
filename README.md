# Lockbox

Scoped, passwordless access to 1Password secrets for your tooling.

1Password gives tooling two options: act as you (the `op` CLI or desktop app
integration), which can read your entire account and re-prompts after about 10
minutes idle, or use a service account, which is scoped and prompt-free but
leaves you storing a long-lived token somewhere.

Lockbox bridges the two. You unlock once with your own identity, which releases
a service account token scoped to a single project's vault. Tooling then reads
that project's secrets without prompting until you lock it or log out. A buggy
or compromised script can only reach the vaults its lockbox's service account
can read, not your whole account.

## Requires

* Linux with correctly configured `XDG_RUNTIME_DIR`
* 1password binary on `PATH`
* "Integrate with other apps" enabled in the desktop app's Developer settings.

## Usage

0. Install

    ```bash
    pip install git+https://github.com/petersuttondev/lockbox.git
    config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/lockbox"
    mkdir -p "$config_dir"
    lockbox schema > "$config_dir"/schema.json
    ```

1. Create a vault containing the secrets you want to control access to.

2. Create a service account that can read the vault and save an access token into
   the vault.

3. Write a configuration file, e.g.;

    ```yaml
    # file: $XDG_CONFIG_HOME/lockbox/config.yaml
    # yaml-language-server: $schema=./schema.json
    account_id: YOUR_ACCOUNT_ID
    lockboxes:
        project-foo:
            service_access_token: op://foo/SECRET_ID/credential
            secrets:
                private_key: op://foo/SECRET_ID/private-key?ssh-format=openssh
                sudo_password: op://foo/SECRET_ID/text
    ```

4. Get secrets in your tooling:

    ```python
    import lockbox


    async def deploy_foo() -> None:
        private_key, sudo_password = await lockbox.get_secrets(
            "project-foo", "private_key", "sudo_password"
        )
        ...
    ```

The first time you run `deploy_foo`, 1Password will ask you for your master
password. Tooling will have passwordless access to secrets until either you lock
the lockbox (`$ lockbox lock project-foo`) or your `XDG_RUNTIME_DIR` is rotated
(e.g., when you log out).

## Security model

When a lockbox is unlocked, its service account token is cached in plain text at
`$XDG_RUNTIME_DIR/lockbox/<lockbox-name>` (mode `0600`, normally on a tmpfs).
Be aware of the following trade-offs:

* **Weaker process isolation than `op`.** The `op` CLI's desktop app
  authorization is tied to a terminal session. The cached token can be read by
  any process running as your user.
* **Tokens outlive the cache.** Locking a lockbox or logging out deletes the
  local copy, but the token itself stays valid until it expires or you revoke
  it in 1Password. If you think a token has leaked, revoke it, don't just lock
  the lockbox.
