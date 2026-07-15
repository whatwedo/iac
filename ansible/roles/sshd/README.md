# sshd

Installs the OpenSSH server and applies a baseline hardening of the SSH daemon.

## What it does

| Task file | Tag | Description |
| --- | --- | --- |
| `1_base.yml` | `base` | Installs `openssh-server` and ensures the `ssh` service is enabled and running. |
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

None. The role is intentionally opinionated; all behaviour is fixed.

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
