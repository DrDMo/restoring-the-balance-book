import os

from restoring_the_balance.paths import DATA_DIR, FIGURES_DIR, REPO_ROOT


def test_repo_root_contains_pyproject():
    assert (REPO_ROOT / "pyproject.toml").is_file()


def test_data_dir_under_repo_root():
    assert DATA_DIR.name in {"Data", os.path.basename(os.environ.get("RTB_DATA_ROOT", "Data"))}


def test_figures_dir_under_repo_root():
    assert FIGURES_DIR.parent == REPO_ROOT
