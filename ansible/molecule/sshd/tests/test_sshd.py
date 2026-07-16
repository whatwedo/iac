"""Testinfra checks for the sshd role."""

def test_openssh_server_installed(host):
    assert host.package("openssh-server").is_installed


def test_ssh_enabled_and_listening(host):
    assert host.service("ssh").is_enabled
    assert host.socket("tcp://0.0.0.0:22").is_listening


def test_sshd_config_hardened(host):
    sshd_config = host.file("/etc/ssh/sshd_config")
    assert sshd_config.exists
    # Baseline hardening applied by 2_hardening.yml.
    assert sshd_config.contains("^PasswordAuthentication no")
    assert sshd_config.contains("^PermitRootLogin no")
