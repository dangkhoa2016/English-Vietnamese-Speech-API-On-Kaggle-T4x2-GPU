from pathlib import Path


def test_tunnel_script_is_default_off_auth_gated_and_coordinator_only() -> None:
    script = Path("scripts/run_tunnel.sh").read_text(encoding="utf-8")
    assert "ENABLE_CLOUDFLARE_TUNNEL" in script
    assert "API_AUTH_REQUIRED" in script
    assert "127.0.0.1:8090" in script
    assert "127.0.0.1:8091" not in script
    assert "127.0.0.1:8092" not in script


def test_tunnel_script_runtime_guards_and_target(tmp_path) -> None:
    import os
    import subprocess

    script = Path("scripts/run_tunnel.sh").resolve()
    base_env = os.environ.copy()

    disabled = subprocess.run(
        ["bash", str(script)],
        env={**base_env, "ENABLE_CLOUDFLARE_TUNNEL": "false"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert disabled.returncode == 2
    assert "disabled" in disabled.stderr.casefold()

    unauthenticated = subprocess.run(
        ["bash", str(script)],
        env={
            **base_env,
            "ENABLE_CLOUDFLARE_TUNNEL": "true",
            "API_AUTH_REQUIRED": "false",
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert unauthenticated.returncode == 3
    assert "refusing" in unauthenticated.stderr.casefold()

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    capture = tmp_path / "args.txt"
    cloudflared = fake_bin / "cloudflared"
    cloudflared.write_text(
        '#!/usr/bin/env bash\nprintf \'%s\\n\' "$@" > "$FAKE_CLOUDFLARED_ARGS"\n',
        encoding="utf-8",
    )
    cloudflared.chmod(0o755)
    allowed = subprocess.run(
        ["bash", str(script)],
        env={
            **base_env,
            "PATH": f"{fake_bin}:{base_env['PATH']}",
            "ENABLE_CLOUDFLARE_TUNNEL": "true",
            "API_AUTH_REQUIRED": "true",
            "FAKE_CLOUDFLARED_ARGS": str(capture),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert allowed.returncode == 0
    args = capture.read_text(encoding="utf-8").splitlines()
    assert args == ["tunnel", "--url", "http://127.0.0.1:8090"]
