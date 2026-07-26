"""Self-check for set_env_var. Run: python -m routers.test_breeze_auth"""
import pathlib
import tempfile

from routers.breeze_auth import set_env_var


def test_updates_existing_key_in_place():
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / ".env"
        p.write_text("DATABASE_URL=postgresql://x\nBREEZE_API_SESSION=old\nBREEZE_API_KEY=abc\n")
        set_env_var(p, "BREEZE_API_SESSION", "new123")
        lines = p.read_text().splitlines()
        assert lines == ["DATABASE_URL=postgresql://x", "BREEZE_API_SESSION=new123", "BREEZE_API_KEY=abc"]


def test_appends_missing_key():
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / ".env"
        p.write_text("DATABASE_URL=postgresql://x\n")
        set_env_var(p, "BREEZE_API_SESSION", "new123")
        assert p.read_text().splitlines() == ["DATABASE_URL=postgresql://x", "BREEZE_API_SESSION=new123"]


def test_creates_file_if_missing():
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / ".env"
        set_env_var(p, "BREEZE_API_SESSION", "new123")
        assert p.read_text().splitlines() == ["BREEZE_API_SESSION=new123"]


if __name__ == "__main__":
    test_updates_existing_key_in_place()
    test_appends_missing_key()
    test_creates_file_if_missing()
    print("ok")
