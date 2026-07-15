# Infrastructure as Code

🚀✨🙌💡🔥🌟🎉🥇👏

Generic Ansible + OpenTofu building blocks for our infrastructure.

## Ansible roles

| Role | Description |
| --- | --- |
| [sshd](ansible/roles/sshd/README.md) | Installs the OpenSSH server and applies baseline SSH hardening |

See [ansible/AGENTS.md](ansible/AGENTS.md) for the conventions all roles follow.

## Testing

Roles are validated with [Molecule](https://ansible.readthedocs.io/projects/molecule/)
(podman driver) + testinfra, and run in CI on every push and pull request
(`.github/workflows/molecule.yml`).

Run a scenario locally:

```bash
cd ansible
molecule test -s sshd
```
