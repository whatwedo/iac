# AGENTS.md — Ansible

Guidance for working in the `ansible/` tree of this Infrastructure-as-Code repo.
(The parallel `tofu/` tree holds the OpenTofu building blocks and is out of scope
here.)

## What this is

Reusable Ansible **building blocks** — roles and thin playbooks — for
provisioning and configuring our Ubuntu/Linux infrastructure, packaged as the
**`whatwedo.iac` collection**. Ansible owns *host and platform* configuration;
application workloads are expected to run on top (e.g. a Kubernetes / GitOps
layer) rather than being deployed directly from here.

This directory *is* the collection root — `galaxy.yml` lives here. Consumers
install it from git (see [README.md](README.md)) and reference content by FQCN,
e.g. `whatwedo.iac.sshd`.

## Layout

```text
ansible/                   # <- collection root
  galaxy.yml               # metadata, version, build_ignore
  meta/runtime.yml         # requires_ansible
  requirements.yml         # external collections / roles pulled from Galaxy
  playbooks/               # thin playbooks: bind a host group -> roles
  roles/                   # the unit of work; almost all logic lives here
    <role>/
      tasks/               # ordered task files (see convention below)
      defaults/main.yml    # tunable defaults, documented
      handlers/main.yml
      meta/main.yml        # galaxy_info: platforms, license
      templates/  files/

  # Development-only. Listed in build_ignore, so it never ships:
  ansible.cfg              # collections_path, roles_path, interpreter
  inventories/<env>/       # one dir per environment (test, production, …)
    hosts                  # host groups
    group_vars/<group>/    # vars.yml + vault.yml (secrets)
    host_vars/<host>/
  molecule/<role>/         # one scenario per role
```

Only `roles/sshd/` exists today — follow this layout as the tree grows.

## What ships, and what doesn't

**Anything a consumer needs at runtime must live inside the collection**:
roles, playbooks, plugins, and their defaults.

**`ansible.cfg`, inventories and secrets do not travel.** Consumers bring their
own. Two consequences worth remembering:

- The repo-local `no_log = ${ANSIBLE_NO_LOG:true}` default is *not* inherited by
  consumers — per-task `no_log: true` on anything touching a secret is the only
  protection that ships.
- Never reference an inventory group or var from inside a role as if it were
  guaranteed; a role's contract is its `defaults/main.yml`.

When adding a dev-only file or directory to this tree, add it to `build_ignore`
in `galaxy.yml`. CI (`.github/workflows/collection.yml`) fails if the built
artifact contains `inventories/`, `molecule/` or `ansible.cfg`.

Bump `version:` in `galaxy.yml` (semver) for any change consumers can observe.

## Local resolution — the collections symlink

Collection tooling only resolves content from a path ending in
`ansible_collections/<namespace>/<name>/`, so the repo carries a checked-in
symlink at `collections/ansible_collections/whatwedo/iac -> ../../../ansible`.
`ansible.cfg` and each `molecule.yml` point `collections_path` at it, which is
why `whatwedo.iac.sshd` resolves against the working tree with no rebuild step.

Do not delete or re-target it, and keep the default collection paths
(`~/.ansible/collections`, `/usr/share/ansible/collections`) on the list —
Molecule's own create/destroy playbooks need `containers.podman` from there.

**The symlink must never be the first entry in a collections path that
something installs into.** `ansible-galaxy collection install` writes to the
first configured path and `shutil.rmtree`s the destination before unpacking:
against the symlink that crashes with *"Cannot call rmtree on a symbolic
link"*, and against a real path inside this tree it would delete the source.

Passing `-p/--collections-path` is **not** enough to avoid this: when
`ansible.cfg` is picked up from the current directory, its `collections_path`
wins and the artifact lands in the working tree regardless of the flag. To
install somewhere specific, run from a directory with no `ansible.cfg` and pin
`ANSIBLE_COLLECTIONS_PATH` — see `.github/workflows/collection.yml`.

`ansible.cfg` therefore leads with `.galaxy/collections` — disposable and
gitignored — and only then `../collections`. Molecule's `ANSIBLE_COLLECTIONS_PATH`
may lead with the symlink because it only ever reads through it.

## Core convention — ordered task files + matching tags

This is the defining pattern of the repo; **every role follows it.**

- Split a role's tasks into ordered files: `1_<name>.yml`, `2_<name>.yml`, …
  Each file does one coherent thing.
- `tasks/main.yml` does nothing but `import_tasks` them in order, and **tags each
  import with a tag named after the file**:

  ```yaml
  ---
  # Task files run in order. Tags let you run a subset, e.g. `--tags hardening`.
  # To add a task file, drop it in this folder and add an import below.

  - import_tasks: 1_hardening.yml
    tags: [hardening]
  ```

- This lets you run just a slice: `ansible-playbook … --tags hardening`.
- To run a single task file *outside* its role's normal ordering, include the
  role with `tasks_from:` (e.g. an update playbook can call a role's
  `update.yml` directly).
- **To add a step:** drop a new numbered file in `tasks/` and add its
  `import_tasks` + tag to `main.yml`. Nothing else picks it up automatically.

## Playbooks are thin

A playbook binds a host group to an ordered list of roles and little else. Keep
logic in roles, not playbooks. Order roles by dependency, and reference roles by
FQCN so it is obvious where each one comes from.

```yaml
- name: Configure hosts
  hosts: all
  become: true
  roles:
    - whatwedo.iac.sshd
    - whatwedo.iac.ufw
```

A playbook placed in `playbooks/` ships with the collection and can be run by
consumers as `ansible-playbook whatwedo.iac.<name>`.

## Variables & secrets

- Role-tunable knobs live in `roles/<role>/defaults/main.yml` (lowest
  precedence) and are the documented surface of the role.
- Environment- and host-specific values live in `inventories/<env>/group_vars`
  and `host_vars`.
- Add `no_log: true` to any task that touches a secret so it can't leak into
  output/logs.

## Idempotency & style

- Use fully-qualified module names (`ansible.builtin.lineinfile`,
  `community.general.ufw`, …).
- Restart services through **handlers** (`notify:`), not an unconditional
  `state: restarted` that churns on every run.
- On `command`/`shell` tasks, set `changed_when:` / `failed_when:` (and
  `creates:` where possible) so runs report honest change state — and prefer a
  real module over shell whenever one exists.
- Keep every task safely re-runnable.
- Declare external collections/roles in `requirements.yml`; install with
  `ansible-galaxy install -r requirements.yml`.

## Testing (target convention)

Validate roles with **Molecule** (podman driver) + **testinfra**:

- One scenario per role under `molecule/<role>/`, reusing the `test` inventory.
- `converge.yml` references the role by **FQCN** (`whatwedo.iac.<role>`), so a
  passing scenario also proves the collection resolves as it will for consumers.
- Assert the observable end state (files exist, correct permissions, config
  content), not task internals.
- Run a scenario with `molecule test -s <role>`.
- Add the scenario name to the matrix in `.github/workflows/molecule.yml` —
  nothing discovers it automatically.

## Security defaults we keep

- SSH: password auth off, root login off, root password locked (see
  `roles/sshd`).
- Firewall default-deny inbound; open only what's needed, scoped to trusted
  networks.
- Generate keys/secrets on the target host or vault them locally; shred any
  transient plaintext.
