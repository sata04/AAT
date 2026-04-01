"""Tests for core.paths module."""

from core.paths import (
    _normalize_base_dir,
    _project_root,
    ensure_cache_dir,
    ensure_graphs_dir,
    ensure_results_dir,
    resolve_base_dir,
)


def test_project_root_returns_repo_root():
    root = _project_root()
    assert root.is_dir()
    assert (root / "core").is_dir()
    assert (root / "pyproject.toml").is_file()


def test_normalize_base_dir_with_file_returns_parent(tmp_path):
    f = tmp_path / "data.csv"
    f.touch()
    assert _normalize_base_dir(f) == tmp_path


def test_normalize_base_dir_with_dir_returns_same(tmp_path):
    assert _normalize_base_dir(tmp_path) == tmp_path


def test_resolve_base_dir_none_returns_project_root():
    assert resolve_base_dir(None) == _project_root()


def test_resolve_base_dir_with_csv_dir(tmp_path):
    result = resolve_base_dir(str(tmp_path))
    assert result == tmp_path


def test_resolve_base_dir_with_file_path(tmp_path):
    f = tmp_path / "data.csv"
    f.touch()
    result = resolve_base_dir(str(f))
    assert result == tmp_path


def test_ensure_results_dir_creates_directory(tmp_path):
    results = ensure_results_dir(str(tmp_path))
    assert results == tmp_path / "results_AAT"
    assert results.is_dir()


def test_ensure_graphs_dir_creates_directory(tmp_path):
    graphs = ensure_graphs_dir(str(tmp_path))
    assert graphs == tmp_path / "results_AAT" / "graphs"
    assert graphs.is_dir()


def test_ensure_cache_dir_creates_directory(tmp_path):
    cache = ensure_cache_dir(str(tmp_path))
    assert cache == tmp_path / "results_AAT" / "cache"
    assert cache.is_dir()


def test_ensure_dirs_are_idempotent(tmp_path):
    for _ in range(2):
        r = ensure_results_dir(str(tmp_path))
        g = ensure_graphs_dir(str(tmp_path))
        c = ensure_cache_dir(str(tmp_path))

    assert r.is_dir()
    assert g.is_dir()
    assert c.is_dir()
