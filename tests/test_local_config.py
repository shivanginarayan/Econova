from scripts.run_backend import load_environment


def test_private_environment_loader_preserves_shell_overrides(tmp_path):
    path = tmp_path / ".env"
    path.write_text('\ufeff# private\nNEBIUS_API_KEY="dummy-local-key"\nexport NEBIUS_MODEL=local-model\nNEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1\nUNRELATED_SECRET=ignored\n', encoding="utf-8")
    env = {"NEBIUS_MODEL": "shell-model"}
    load_environment(path, env)
    assert env["NEBIUS_API_KEY"] == "dummy-local-key"
    assert env["NEBIUS_MODEL"] == "shell-model"
    assert "UNRELATED_SECRET" not in env


def test_missing_local_env_is_optional(tmp_path):
    env = {}
    load_environment(tmp_path / "missing", env)
    assert env == {}
