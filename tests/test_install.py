# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import zipfile

import mock_server

from cjdk import _conf, _install


def test_install_file(tmp_path):
    content = b"\n\n\r\r\n\n"

    def check(filepath):
        with open(filepath, "rb") as fp:
            assert fp.read() == content

    with mock_server.start(
        file_endpoint="/testfile", file_data=content
    ) as server:
        cachedpath = _install.install_file(
            "testprefix",
            "testname",
            server.url("/testfile"),
            "cachedfile",
            _conf.configure(
                cache_dir=tmp_path / "cache", _allow_insecure_for_testing=True
            ),
            ttl=2**63,
            checkfunc=check,
        )

    assert cachedpath.name == "cachedfile"
    assert cachedpath.parent.parent.samefile(
        tmp_path / "cache" / "v0" / "testprefix"
    )
    check(cachedpath)

    def check_not_called(filepath):
        assert False

    with mock_server.start() as server:
        cachedpath2 = _install.install_file(
            "testprefix",
            "testname",
            server.url("/testfile"),
            "cachedfile",
            _conf.configure(cache_dir=tmp_path / "cache"),
            ttl=2**63,
            checkfunc=check_not_called,
        )

    assert cachedpath2 == cachedpath
    check(cachedpath)


def test_install_dir(tmp_path):
    (tmp_path / "origfile").touch()
    zip = tmp_path / "orig.zip"
    with zipfile.ZipFile(zip, "x") as zf:
        zf.write(tmp_path / "origfile", "testfile")
    with open(zip, "rb") as f:
        zipdata = f.read()

    def check(filepath):
        with open(filepath, "rb") as fp:
            assert fp.read() == zipdata

    with mock_server.start(
        file_endpoint="/test.zip", file_data=zipdata
    ) as server:
        cacheddir = _install.install_dir(
            "testprefix",
            "testname",
            "zip+" + server.url("/test.zip"),
            _conf.configure(
                cache_dir=tmp_path / "cache", _allow_insecure_for_testing=True
            ),
            checkfunc=check,
        )

    assert (cacheddir / "testfile").is_file()
    assert cacheddir.parent.samefile(tmp_path / "cache" / "v0" / "testprefix")

    def check_not_called(filepath):
        assert False

    with mock_server.start() as server:
        cacheddir2 = _install.install_dir(
            "testprefix",
            "testname",
            "zip+" + server.url("/test.zip"),
            _conf.configure(cache_dir=tmp_path / "cache"),
            checkfunc=check_not_called,
        )

    assert cacheddir2 == cacheddir
