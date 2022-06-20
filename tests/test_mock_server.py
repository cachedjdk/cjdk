# This file is part of cachedjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import mock_server
import requests


def test_shutdown():
    with mock_server.start("/test", {}) as server:
        pass


def test_endpoint_and_count():
    with mock_server.start("/test", {"hello": "world"}) as server:
        assert server.request_count() == 0

        response = requests.get(server.endpoint_url())
        data = response.json()
        assert data == {"hello": "world"}
        assert server.request_count() == 1
