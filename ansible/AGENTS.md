# AGENTS.md — Ansible

Guidance for working in the `ansible/` tree of this Infrastructure-as-Code repo.
(The parallel `tofu/` tree holds the OpenTofu building blocks and is out of scope
here.)

## What this is

Reusable Ansible **building blocks** — roles and thin playbooks — for
provisioning and configuring our Ubuntu/Linux infrastructure. Ansible owns
*host and platform* configuration; application workloads are expected to run on
top (e.g. a Kubernetes / GitOps layer) rather than being deployed directly from
here.

## Layout

```text
ansible/
  ansible.cfg            # roles_path, default inventory, interpreter   (add when needed)
  requirements.yml       # external collections / roles pulled from Galaxy
  inventories/<env>/      # one dir per environment (test, production, …)
    hosts                # host groups
    group_vars/<group>/  # vars.yml + vault.yml (secrets)
    host_vars/<host>/
  playbooks/             # thin playbooks: bind a host group -> roles
  roles/                 # the unit of work; almost all logic lives here
    <role>/
      tasks/             # ordered task files (see convention below)
      defaults/main.yml  # tunable defaults, documented
      handlers/main.yml
      templates/  files/
```

Only `roles/sshd/` exists today — follow this layout as the tree grows.

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
logic in roles, not playbooks. Order roles by dependency.

```yaml
- name: Configure hosts
  hosts: all
  become: true
  roles:
    - sshd
    - ufw
```

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
- Assert the observable end state (files exist, correct permissions, config
  content), not task internals.
- Run a scenario with `molecule test -s <role>`.

## Security defaults we keep

- SSH: password auth off, root login off, root password locked (see
  `roles/sshd`).
- Firewall default-deny inbound; open only what's needed, scoped to trusted
  networks.
- Generate keys/secrets on the target host or vault them locally; shred any
  transient plaintext.
