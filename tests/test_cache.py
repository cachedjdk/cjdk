from cachedjdk import _cache
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
import sys
import time
import tqdm


def test_default_cachedir(monkeypatch):
    f = _cache.default_cachedir
    monkeypatch.setenv("CACHEDJDK_CACHE_DIR", "/a/b/c")
    assert f() == Path("/a/b/c")
    monkeypatch.delenv("CACHEDJDK_CACHE_DIR")
    assert Path.home() in f().parents
    assert "cache" in str(f().relative_to(Path.home())).lower()


def test_url_to_key():
    f = _cache.url_to_key
    assert f("https://x.com/a/b.json") == ("x.com", "a", "b.json")
    assert f("https://x.com/a%2Bb/c.json") == ("x.com", "a+b", "c.json")


def test_call_with_optional_tqdm():
    f = _cache._call_with_optional_tqdm

    def assert_tqdm(x):
        assert x is not None
        assert hasattr(x, "update")
        assert hasattr(x, "reset")

    def assert_none(x):
        assert x is None

    f(assert_tqdm, True)
    f(assert_tqdm, tqdm.std.tqdm())
    f(assert_tqdm, tqdm.asyncio.tqdm())
    f(assert_none, None)
    f(assert_none, False)


def test__default_cachedir():
    f = _cache._default_cachedir
    assert Path.home() in f().parents
    assert "cache" in str(f().relative_to(Path.home())).lower()


def test_local_app_data(monkeypatch):
    f = _cache._local_app_data
    monkeypatch.setenv("LOCALAPPDATA", "/a/b/c")
    assert f() == Path("/a/b/c")
    monkeypatch.delenv("LOCALAPPDATA")
    assert f() == Path.home() / "AppData" / "Local"


def test_macos_cachedir():
    assert (
        _cache._macos_cachedir()
        == Path.home() / "Library" / "Caches" / "CachedJDK"
    )


def test_xdg_cachedir(monkeypatch):
    f = _cache._xdg_cachedir
    monkeypatch.setenv("XDG_CACHE_HOME", "/a/b/c")
    assert f() == Path("/a/b/c/cachedjdk")
    monkeypatch.delenv("XDG_CACHE_HOME")
    assert f() == Path.home() / ".cache" / "cachedjdk"


def test_file_exists_and_is_fresh(tmp_path):
    f = _cache._file_exists_and_is_fresh
    path = tmp_path / "test"
    assert not f(path, ttl=0)
    assert not f(path, ttl=2**63)
    path.touch()
    assert f(path, ttl=1)
    time.sleep(0.1)
    assert not f(path, ttl=0.05)
    assert f(path, ttl=1)


def test_key_directory():
    f = _cache._key_directory
    assert f("a", ("b",)) == Path("a/b")


def test_key_tmpdir():
    f = _cache._key_tmpdir
    assert f("a", ("b",)) == Path("a/fetching/b")


def test_check_key():
    f = _cache._check_key
    f(("a", "b"))
    with pytest.raises(ValueError):
        f(("a/",))
    with pytest.raises(ValueError):
        f(
            (
                "b",
                "a\\",
            )
        )


def test_swap_in_fetched_file(tmp_path):
    dest = tmp_path / "a" / "b" / "target"
    src = tmp_path / "tmpfile"
    src.touch()
    _cache._swap_in_fetched_file(dest, src, timeout=0)
    assert dest.is_file()
    assert not src.is_file()

    # With dest existing
    src.touch()
    _cache._swap_in_fetched_file(dest, src, timeout=0)
    assert dest.is_file()
    assert not src.is_file()

    # With dest initially open
    exec = ThreadPoolExecutor()

    def close_after_delay(f):
        time.sleep(0.1)
        f.close()

    src.touch()
    with open(dest) as fp:
        exec.submit(close_after_delay, fp)
        _cache._swap_in_fetched_file(dest, src, timeout=10)
        assert dest.is_file()
        assert not src.is_file()

    exec.shutdown()

    # With dest left open
    if sys.platform == "win32":
        src.touch()
        with open(dest) as fp:
            with pytest.raises(OSError):
                _cache._swap_in_fetched_file(dest, src, timeout=0.1)


def test_move_in_fetched_directory(tmp_path):
    dest = tmp_path / "a" / "b" / "target"
    src = tmp_path / "tmpdir"
    src.mkdir()
    _cache._move_in_fetched_directory(dest, src)
    assert dest.is_dir()
    assert not src.is_dir()


def test_wait_for_dir_to_vanish(tmp_path):
    path = tmp_path / "testdir"
    path.mkdir()
    exec = ThreadPoolExecutor()

    def rmdir_after_delay(p):
        time.sleep(0.1)
        p.rmdir()

    exec.submit(rmdir_after_delay, path)
    _cache._wait_for_dir_to_vanish(path, 10)
    exec.shutdown()

    path.mkdir()
    with pytest.raises(Exception):
        _cache._wait_for_dir_to_vanish(path, 0.1)


def test_backoff_seconds():
    f = _cache._backoff_seconds
    assert list(f(1, 0)) == [-1]
    assert list(f(1, 1)) == [1, -1]
    assert list(f(1, 0.1)) == [0.1, -1]
    assert list(f(1, 10, factor=2)) == [1, 2, 4, 3, -1]
