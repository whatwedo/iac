# Infrastructure as Code

🚀✨🙌💡🔥🌟🎉🥇👏

Generic Ansible + OpenTofu building blocks for our infrastructure.

## Ansible

Reusable roles and thin playbooks for provisioning and configuring hosts.
See [ansible/README.md](ansible/README.md) for the roles, the development
environment ([iac-shell](https://github.com/whatwedo/iac-shell)), and testing.

## Linting & CI

GitHub Actions run on every push to `main` and on pull requests:

- **[MegaLinter](https://megalinter.io)** (`terraform` flavor) lints Ansible,
  OpenTofu/Terraform, YAML, Markdown and shell, and scans the repo for secrets.
  Auto-fixable issues are proposed back as a pull request. Tune it via
  [`.mega-linter.yml`](.mega-linter.yml).
- **Molecule** exercises the Ansible roles (see `ansible/`).

Run MegaLinter locally with [`mega-linter-runner`](https://megalinter.io/latest/mega-linter-runner/)
(needs Docker):

```bash
npx mega-linter-runner --flavor terraform
```
