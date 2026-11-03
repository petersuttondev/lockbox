import subprocess
import tomllib
from pathlib import Path

from cleek import task


@task
def install() -> None:
    project_dir = _get_project_dir()
    subprocess.run(
        (
            project_dir / "venv/bin/pip",
            "install",
            "--editable",
            project_dir,
        ),
        stdin=subprocess.DEVNULL,
        check=True,
    )


@task
def uninstall() -> None:
    project_dir = _get_project_dir()
    with open(project_dir / "pyproject.toml", "rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)
    subprocess.run(
        (
            project_dir / "venv/bin/pip",
            "uninstall",
            pyproject["project"]["name"],
        ),
        stdin=subprocess.DEVNULL,
        check=True,
    )


_project_dir: Path | None = None


def _get_project_dir() -> Path:
    global _project_dir
    if _project_dir is None:
        _project_dir = Path(__file__).resolve(strict=True).parent
    return _project_dir
