# Ansible

Reusable Ansible **building blocks** — roles and thin playbooks — for
provisioning and configuring our Debian/Linux infrastructure.

See [AGENTS.md](AGENTS.md) for the conventions all roles follow.

## Roles

| Role | Description |
| --- | --- |
| [sshd](roles/sshd/README.md) | Installs the OpenSSH server and applies baseline SSH hardening |

## Development environment — iac-shell

All the tooling (Ansible, Molecule, linters/formatters like `yamllint` and
`prettier`, …) is bundled in [iac-shell](https://github.com/whatwedo/iac-shell),
a containerized shell — so you don't install any of it on your host. The only
requirement is [podman](https://podman.io/).

Load the `wwd` helper (add the line to your `~/.bashrc` to make it permanent):

```bash
source <(curl -s https://raw.githubusercontent.com/whatwedo/iac-shell/refs/heads/main/source.sh)
```

Then drop into the shell from the repo root:

```bash
wwd
```

`wwd` mounts your current directory at `/workspace` and wires through the podman
socket, so Molecule can start test containers from inside the shell. Pass
`--pull` to force-refresh the image:

```bash
wwd --pull
```

Run the Ansible and Molecule commands below from inside this shell.

## Testing

Roles are validated with [Molecule](https://ansible.readthedocs.io/projects/molecule/)
(podman driver) + testinfra, and run in CI on every push and pull request
(`.github/workflows/molecule.yml`).

Scenarios run against the
[iac-test-debian](https://github.com/whatwedo/iac-test-debian) image
(`ghcr.io/whatwedo/iac-test-debian:13`) — a systemd-enabled Debian 13 container
with a preconfigured `test-admin` user — so tests can assert real service state
(e.g. that `sshd` is actually running).

Each scenario reuses the shared [`test` inventory](inventories/test) rather than
inlining values in `molecule.yml`: `provisioner.inventory.links` pulls in its
`hosts`, `group_vars/` and `host_vars/`, so a role is exercised against the same
groups and variables a real run would use. The Molecule platform is named to
match a host in that inventory so its host/group vars apply.

Run a scenario (from inside `wwd`):

```bash
cd ansible
molecule test -s sshd
```
