"""Testinfra checks for the sshd role.

The config-content check renders the role's own defaults/main.yml +
templates/sshd_config.j2 with Jinja2 (no Ansible runtime involved) and diffs
the resulting directive lines against what's actually deployed on the host.
That means the test fails the moment the deployed config drifts from the
role's source of truth in either direction: a missing hardening directive,
or an unwanted extra one - which is the guarantee the sshd hardening ticket
asks for.
"""

from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

# tests/ -> sshd (molecule scenario) -> molecule -> ansible -> roles/sshd
ROLE_DIR = Path(__file__).resolve().parents[3] / "roles" / "sshd"


def _ternary(value, true_val, false_val):
    """Minimal stand-in for Ansible's `ternary` filter used in the template."""
    return true_val if value else false_val


def _comment(value):
    """Minimal stand-in for Ansible's `comment` filter (only used for the
    ansible_managed header, which is filtered out as a comment line below
    anyway)."""
    return f"# {value}"


def render_expected_config():
    defaults = yaml.safe_load((ROLE_DIR / "defaults" / "main.yml").read_text())
    env = Environment(
        loader=FileSystemLoader(str(ROLE_DIR / "templates")),
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined,
    )
    env.filters["ternary"] = _ternary
    env.filters["comment"] = _comment
    template = env.get_template("sshd_config.j2")
    return template.render(ansible_managed="Ansible managed", **defaults)


def directive_lines(config_text):
    """Non-comment, non-blank lines - i.e. what sshd actually parses,
    regardless of formatting/comment differences."""
    return sorted(
        line.strip()
        for line in config_text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


def test_openssh_server_installed(host):
    assert host.package("openssh-server").is_installed


def test_ssh_enabled_and_listening(host):
    assert host.service("ssh").is_enabled
    assert host.socket("tcp://0.0.0.0:22").is_listening


def test_sshd_config_permissions(host):
    sshd_config = host.file("/etc/ssh/sshd_config")
    assert sshd_config.exists
    assert sshd_config.user == "root"
    assert sshd_config.group == "root"
    assert sshd_config.mode == 0o600


def test_sshd_config_matches_role_exactly(host):
    """No unwanted config may creep in: every directive in
    /etc/ssh/sshd_config must come from the role's own template+defaults -
    nothing more, nothing less."""
    expected = directive_lines(render_expected_config())
    # The file is root:root, mode 0600 - test-admin needs sudo to read it.
    with host.sudo():
        actual_text = host.file("/etc/ssh/sshd_config").content_string
    actual = directive_lines(actual_text)
    assert actual == expected


def test_sshd_syntax_is_valid(host):
    with host.sudo():
        result = host.run("sshd -t")
    assert result.rc == 0, result.stderr
