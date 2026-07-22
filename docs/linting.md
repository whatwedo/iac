# Linting & CI

GitHub Actions run on every push to `main` and on pull requests:

- **[MegaLinter](https://megalinter.io)** (`terraform` flavor) lints Ansible,
  OpenTofu/Terraform, YAML, Markdown and shell, and scans the repo for secrets.
  Auto-fixable issues are proposed back as a pull request. Tune it via
  [`.mega-linter.yml`](../.mega-linter.yml).
- **Molecule** exercises the Ansible roles (see [`ansible/`](../ansible/README.md)).

Run MegaLinter locally with [`mega-linter-runner`](https://megalinter.io/latest/mega-linter-runner/)
(needs Docker):

```bash
npx mega-linter-runner --flavor terraform
```

## MegaLinter

MegaLinter auto-detects the file types in the repo and runs the linters bundled
in the [`terraform` flavor](https://megalinter.io/latest/flavors/terraform/).
Behaviour is tuned in [`.mega-linter.yml`](../.mega-linter.yml), and the workflow
lives in [`.github/workflows/mega-linter.yml`](../.github/workflows/mega-linter.yml).

The table below lists the checks relevant to this Ansible + OpenTofu codebase.

| Check | Linter(s) | What it checks |
| --- | --- | --- |
| Ansible | ansible-lint | Ansible role/playbook errors & best practices |
| Terraform / OpenTofu | terraform fmt, tflint, terrascan, terragrunt | Tofu/Terraform formatting, validity & security misconfig |
| YAML | yamllint, prettier | YAML syntax, style & formatting |
| Markdown | markdownlint | Markdown style & formatting |
| Bash | shellcheck, shfmt | Shell script bugs & formatting |
| Dockerfile | hadolint | Dockerfile best practices |
| Python | bandit | Python security issues |
| Secrets | gitleaks, kingfisher | Leaked credentials/secrets in the repo |
| Security / IaC | trivy, checkov | Vulnerabilities & IaC misconfigurations |
| Copy-paste | jscpd | Excessive duplicated code |

Disabled checks:

| Check | Linter | Why disabled |
| --- | --- | --- |
| Spelling | cspell | Too noisy for this repo (`DISABLE: SPELL`) |
| Vulnerability scan | grype | DB fails to hydrate in CI; trivy already covers this (`DISABLE_LINTERS: REPOSITORY_GRYPE`) |

## Molecule

[Molecule](https://ansible.readthedocs.io/projects/molecule/) exercises the
Ansible roles. See [`ansible/README.md`](../ansible/README.md) for how to run it.
