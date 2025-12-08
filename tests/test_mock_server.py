# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import mock_server
import requests


def test_shutdown():
    with mock_server.start():
        pass


def test_endpoint_and_count():
    with mock_server.start(data={"hello": "world"}) as server:
        assert server.request_count() == 0

        response = requests.get(server.url("/test"))
        data = response.json()
        assert data == {"hello": "world"}
        assert server.request_count() == 1


def test_download():
    size = 1024 * 1024
    with mock_server.start(download_size=size) as server:
        response = requests.get(server.url("/download"))
        assert int(response.headers["content-length"]) == size
        for chunk in response.iter_content(chunk_size=4096):
            assert chunk == b"*" * len(chunk)
            size -= len(chunk)
        assert size == 0


def test_file():
    with mock_server.start() as server:
        response = requests.get(server.url("/file.txt"))
        assert response.content == b"hello"
