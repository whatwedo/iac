# Dependency updates

[Renovate](https://docs.renovatebot.com/) runs as a self-hosted GitHub Action and
opens pull requests for outdated dependencies. Every Renovate PR is gated by the
same [MegaLinter and Molecule checks](linting.md) as a human one.

- Workflow: [`.github/workflows/renovate.yml`](../.github/workflows/renovate.yml)
- Update policy: [`.github/renovate.json`](../.github/renovate.json)

Why it exists: all `uses:` refs in this repo are pinned to a commit SHA (zizmor's
`unpinned-uses` audit requires it), so every manual bump means resolving tag → SHA
by hand and rewriting the trailing `# vX.Y.Z` comment. Renovate does that
mechanically, and keeps the comment in sync.

## What is managed

| Manager            | Files                                                             | Contents                                       |
|--------------------|-------------------------------------------------------------------|------------------------------------------------|
| `github-actions`   | `.github/workflows/*.yml`                                         | Action refs — SHA pin + version comment        |
| `pip_requirements` | [`ansible/requirements-dev.txt`](../ansible/requirements-dev.txt) | `ansible-core`, `molecule`, `pytest-testinfra` |
| `ansible-galaxy`   | [`ansible/requirements.yml`](../ansible/requirements.yml)         | Galaxy collections (`containers.podman`)       |
| `terraform`        | `tofu/**.tf`                                                      | Inert until the first `.tf` file lands         |

Both requirements files are pinned exactly (`==` / `version:`) — Renovate skips
unpinned entries, and exact pins are what make a CI run reproducible.

**Not** managed, update these by hand:

- `ghcr.io/whatwedo/iac-test-debian:13` in `ansible/molecule/*/molecule.yml` — a
  Debian major is a deliberate decision, not a dependency bump.
- `python-version` in `.github/workflows/molecule.yml`, which is coupled to
  `interpreter_python` in `ansible/ansible.cfg`. Note that `ansible-core` 2.21
  already requires Python ≥ 3.12, so CI sits exactly on the floor — the next
  `ansible-core` bump may force a Python bump, and both files then need editing
  together. That is the main reason those bumps are not automerged.

## Update policy

| Update                                  | Behaviour                                   |
|-----------------------------------------|---------------------------------------------|
| Actions — minor, patch, digest          | One grouped PR, automerged once CI is green |
| Actions — major                         | Individual PR, needs review                 |
| Ansible/Python toolchain — minor, patch | One grouped PR, automerged once CI is green |
| Ansible/Python toolchain — major        | Individual PR, needs review                 |

Majors are never automerged: action majors change inputs and outputs, and
`ansible-core`/`molecule` majors can move the supported Python range.

Renovate keeps a **Dependency Dashboard** issue listing everything it sees,
including updates it is holding back. That issue is the place to trigger a
retry or unblock a PR.

Automerge relies on two repository settings: *Allow auto-merge* (Settings →
General) and a branch protection rule on `main` requiring the `MegaLinter` and
`molecule (sshd)` checks. Without the required checks there is nothing to gate a
merge on — if the protection rule is ever removed, set `automerge` to `false` in
`.github/renovate.json`.

## Running it manually

Actions → **Renovate** → *Run workflow*. Two inputs:

- `dryRun` — log what would happen without creating branches or PRs. Use this
  after changing `.github/renovate.json`.
- `logLevel` — set to `debug` to see which files each manager matched.

Otherwise it runs Mondays at 04:00 UTC. That cron is the only schedule:
`.github/renovate.json` intentionally has no `schedule` key, so a manual run
always does work rather than silently no-op'ing outside a configured window.

A push to `main` that touches the workflow or the config also triggers a run, so
policy changes take effect without waiting a week.

## Authentication

Renovate uses a fine-grained PAT from the `RENOVATE_TOKEN` repository secret,
scoped to this repository, with these permissions:

| Permission    | Access         | Why                                     |
|---------------|----------------|-----------------------------------------|
| Contents      | Read and write | Push update branches                    |
| Pull requests | Read and write | Open, update and automerge PRs          |
| Issues        | Read and write | Maintain the Dependency Dashboard issue |
| Workflows     | Read and write | Edit files under `.github/workflows/`   |

The automatic `GITHUB_TOKEN` cannot be used: it may not write workflow files, and
PRs it opens do not trigger `pull_request` workflows — so MegaLinter and Molecule
would never run on a Renovate PR, which is exactly the check automerge depends
on.

Two failure modes worth knowing:

- **The PAT expires.** Renovate then fails silently apart from a red run in the
  Actions tab. Note the expiry when creating the token.
- **GitHub disables scheduled workflows** in a repository with no activity for 60
  days. Re-enable from the Actions tab.
