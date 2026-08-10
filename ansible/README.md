# whatwedo.iac — Ansible Collection

Reusable Ansible **building blocks** — roles and thin playbooks — for
provisioning and configuring our Debian/Linux infrastructure, packaged as the
`whatwedo.iac` collection.

See [AGENTS.md](AGENTS.md) for the conventions all roles follow.

## Contents

| Role                                       | FQCN                | Description                                                    |
|--------------------------------------------|---------------------|----------------------------------------------------------------|
| [sshd](roles/sshd/README.md)               | `whatwedo.iac.sshd` | Installs the OpenSSH server and applies baseline SSH hardening |

## Installing

The collection is not published to Ansible Galaxy (yet), so consumers install it
straight from git. Add it to your `requirements.yml` — the `#/ansible` fragment
points at the collection inside this monorepo, and the trailing ref pins the
version:

```yaml
---
collections:
  - name: git+https://github.com/whatwedo/iac.git#/ansible
    type: git
    version: v0.1.0
```

```bash
ansible-galaxy collection install -r requirements.yml
```

Always pin a tag rather than tracking `main`, so an upgrade is a reviewable
one-line change.

## Using a role

Reference roles by their fully-qualified collection name. Playbooks stay thin —
they bind a host group to an ordered list of roles and little else:

```yaml
---
- name: Configure hosts
  hosts: all
  become: true
  roles:
    - whatwedo.iac.sshd
```

Every role splits its work into ordered, tagged task files, so you can run a
single slice:

```bash
ansible-playbook -i inventories/production site.yml --tags hardening
```

Note that `ansible.cfg`, inventories and secrets **do not** travel with the
collection — those stay in the consuming repo.

## Layout

```text
ansible/                     # <- the collection root (galaxy.yml lives here)
  galaxy.yml                 # collection metadata + build_ignore
  meta/runtime.yml           # minimum supported ansible-core
  roles/<role>/              # the unit of work; almost all logic lives here
  playbooks/                 # optional shipped playbooks, callable as whatwedo.iac.<name>

  # Development-only — excluded from the built artifact via build_ignore:
  ansible.cfg
  inventories/test/          # shared test inventory, reused by Molecule
  molecule/<role>/           # one scenario per role
```

Because collection tooling resolves content from a path ending in
`ansible_collections/<namespace>/<name>/`, the repo carries a checked-in symlink:

```text
collections/ansible_collections/whatwedo/iac -> ../../../ansible
```

`ansible.cfg` and the Molecule scenarios point `collections_path` at it, which
is what makes `whatwedo.iac.sshd` resolve against your working tree — edits to a
role take effect immediately, with no rebuild or reinstall.

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

Scenarios converge the role through its **FQCN**, so a passing test also proves
the collection resolves the way it will for a consumer.

Run a scenario (from inside `wwd`):

```bash
cd ansible
molecule test -s sshd
```

## Releasing

1. Bump `version:` in [galaxy.yml](galaxy.yml) following semver.
2. Merge to `main`.
3. Tag the release: `git tag v<version> && git push origin v<version>`.
4. Bump the pinned `version:` in the consuming repo's `requirements.yml`.

`.github/workflows/collection.yml` builds and installs the artifact on every PR,
so a broken `galaxy.yml` or an artifact that accidentally ships the dev-only
inventory fails CI before it reaches a tag.
