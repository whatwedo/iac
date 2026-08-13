# sshd

Installs the OpenSSH server and applies a baseline hardening of the SSH daemon.

## What it does

| Task file         | Tag         | Description                                                                                 |
| ----------------- | ----------- | ------------------------------------------------------------------------------------------- |
| `1_base.yml`      | `base`      | Installs `openssh-server` and ensures the `ssh` service is enabled and running.             |
| `2_hardening.yml` | `hardening` | Disables password authentication, disables root login, and locks the root account password. |

Changes to the SSH daemon config notify the `Restart sshd` handler, so the
service is restarted only when its configuration actually changes.

## Requirements

- Debian/Ubuntu target (uses `ansible.builtin.apt` and the `ssh` systemd unit).
- Privilege escalation (`become: true`).

> ⚠️ This role turns off SSH password authentication and root login. Make sure a
> non-root user with valid SSH keys and sudo access already exists on the host,
> or you can lock yourself out.

## Variables

All defaults live in `defaults/main.yml` and can be overridden per group or
host via the standard `group_vars`/`host_vars` mechanism - no changes to the
role itself are needed.

Before using this role on a host, review at least:

- `sshd_port`, `sshd_address_family`, `sshd_listen_addresses` - the actual
  listener config for the target host.
- `sshd_pubkey_accepted_algorithms`, `sshd_pubkey_auth_options` - which key
  types are accepted and how they're enforced. Default is the SOFT tier
  (hardware + software keys, no enforcement beyond FIDO2 defaults); the
  HYBRID and HARD variants are commented out directly in `defaults/main.yml`.
- `sshd_allow_groups`, `sshd_allow_users`, `sshd_deny_groups`,
  `sshd_deny_users` - who is actually permitted to log in.

Misconfiguring any of these can lock legitimate users out or leave the host
reachable with unintended keys.

## Usage

```yaml
- name: Configure hosts
  hosts: all
  become: true
  roles:
    - sshd
```

Run a single slice with tags, e.g. only the hardening step:

```bash
ansible-playbook -i inventory playbook.yml --tags hardening
```

## Testing

A Molecule scenario lives in `ansible/molecule/sshd/` (podman driver +
testinfra):

```bash
cd ansible
molecule test -s sshd
```
