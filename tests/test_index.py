from cachedjdk import _index
import json
import pytest
import urllib


def test_index(tmp_path):
    index = _index.index(cachedir=tmp_path)
    assert "linux" in index


def test_available_jdks(tmp_path):
    index = _index.index(cachedir=tmp_path)
    jdks = _index.available_jdks(index, os="linux", arch="x86_64")
    assert len(jdks)
    assert len(jdks[0]) == 2
    assert isinstance(jdks[0][0], str)
    assert isinstance(jdks[0][1], str)


def test_jdk_url(tmp_path):
    index = _index.index(cachedir=tmp_path)
    assert _index.jdk_url(
        index, "adoptium", "17.0.1", os="linux", arch="amd64"
    ) == urllib.parse.urlparse(
        "tgz+https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.1%2B12/OpenJDK17U-jdk_x64_linux_hotspot_17.0.1_12.tar.gz"
    )


def test_cached_index(tmp_path):
    url = "https://raw.githubusercontent.com/coursier/jvm-index/master/index.json"
    path = _index._cached_index(url, 86400, tmp_path)
    assert path.is_file()
    assert path.samefile(
        tmp_path
        / _index._INDEX_KEY_PREFIX
        / "raw.githubusercontent.com"
        / "coursier"
        / "jvm-index"
        / "master"
        / "index.json"
        / _index._INDEX_FILENAME
    )
    _index._read_index(path)  # Should not raise


def test_fetch_index(tmp_path):
    url = "https://raw.githubusercontent.com/coursier/jvm-index/master/index.json"
    path = tmp_path / "test.json"
    _index._fetch_index(url, path, progress=None)
    assert path.is_file()
    _index._read_index(path)  # Should not raise


def test_read_index(tmp_path):
    data = {
        "a": ["b", "c"],
    }
    path = tmp_path / "test.json"
    with open(path, "w") as outfile:
        json.dump(data, outfile)
    assert _index._read_index(path) == data


def test_normalize_os():
    f = _index._normalize_os
    assert f("Win32") == "windows"
    assert f("macOS") == "darwin"
    assert f("aix100") == "aix"
    assert f("solaris100") == "solaris"


def test_normalize_arch():
    f = _index._normalize_arch
    aliases = {
        "x86": ["386", "i386", "586", "i586", "686", "i686", "X86"],
        "amd64": ["x64", "x86_64", "x86-64", "AMD64"],
        "arm64": ["aarch64", "ARM64"],
    }
    for k, v in aliases.items():
        for a in v:
            assert f(a) == k

    assert f("ia64") == "ia64"  # Not amd64
    assert f("ppc64le") != f("ppc64")
    assert f("ppcle") != f("ppc")
    assert f("s390x") != f("s390")


def test_match_version():
    f = _index._match_version
    assert f("adoptium", ["10", "11.0", "11.1", "1.12.0"], "11") == "11.1"
    assert f("adoptium", ["10", "11.0", "11.1", "1.12.0"], "12") == "1.12.0"
    assert f("graalvm", ["10", "11.0", "11.1", "1.12.0"], "11") == "11.1"
    assert f("graalvm", ["10", "11.0", "11.1", "1.12.0"], "1") == "1.12.0"


def test_normalize_version():
    f = _index._normalize_version
    assert f("1") == (1,)
    assert f("1.0") == (1, 0)
    assert f("1-0") == (1, 0)
    assert f("1", remove_prefix_1=True) == ()
    assert f("1.8", remove_prefix_1=True) == (8,)
    assert f("1.8.0", remove_prefix_1=True) == (8, 0)
    with pytest.raises(ValueError):
        f("1.8u300", remove_prefix_1=True)


def test_is_version_compatible_with_spec():
    f = _index._is_version_compatible_with_spec
    assert f("1", "1")
    assert not f("1", "2")
    assert f("1.0", "1")
    assert not f("1", "1.0")
    assert not f("1.0", "1.1")
    assert not f("1.1", "1.0")
    assert f("11.1.2.3", "11")
    assert f("11.1.2.3", "11.1")
    assert not f("11.1.2.3", "11.1.2.3.0")
