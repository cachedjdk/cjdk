# This file is part of cjdk.
# Copyright 2022, Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import os
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import flask
import requests
from werkzeug.debug import DebuggedApplication
from werkzeug.serving import make_server

__all__ = [
    "port",
    "start",
]


_PORT = int(os.environ.get("CJDK_TEST_PORT", "5000"))


def port():
    return _PORT


@contextmanager
def start(
    *,
    endpoint="/test",
    data={},
    download_endpoint="/download",
    download_size=0,
    file_endpoint="/file.txt",
    file_data=b"hello",
):
    server = _start(
        endpoint,
        data,
        download_endpoint,
        download_size,
        file_endpoint,
        file_data,
    )
    try:
        yield server
    finally:
        server._shutdown()


def _start(
    endpoint, data, download_endpoint, download_size, file_endpoint, file_data
):
    def run_server(endpoint, data):
        exec = ThreadPoolExecutor()
        server = None
        app = flask.Flask("mock_server")
        request_count = 0

        @app.route("/health")
        def health():
            return flask.jsonify({})

        @app.route("/shutdown")
        def shutdown():
            nonlocal server
            # The shutdown() method will block until the server exits, so we
            # need to run it from another thread.
            exec.submit(server.shutdown)
            return "Exiting"

        @app.route(endpoint)
        def test():
            nonlocal request_count
            request_count += 1
            return flask.jsonify(data)

        @app.route("/request_count")
        def count():
            nonlocal request_count
            return flask.jsonify({"count": request_count})

        @app.route(download_endpoint)
        def download():
            def generate():
                remaining = download_size
                chunk_size = 4096
                while remaining > chunk_size:
                    yield b"*" * chunk_size
                    remaining -= chunk_size
                yield b"*" * remaining

            return flask.Response(
                generate(),
                content_type="application/octet-stream",
                headers={
                    "content-disposition": "attachment; filename=test.zip",
                    "content-length": download_size,
                },
            )

        @app.route(file_endpoint)
        def file():
            return flask.Response(
                file_data,
                content_type="application/octet-stream",
                headers={
                    "content-disposition": "attachment; filename=test.zip",
                },
            )

        app = DebuggedApplication(app)
        server = make_server("127.0.0.1", _PORT, app)
        server.serve_forever(poll_interval=0.1)
        exec.shutdown()

    th = threading.Thread(target=run_server, args=(endpoint, data))
    th.start()
    server = _MockServer(_PORT, endpoint, th)

    # Now wait until the server comes up
    while True:
        try:
            response = requests.get(server.url("/health"))
            if response.status_code == 200:
                return server
        except Exception:
            pass


class _MockServer:
    def __init__(self, port, endpoint, thread):
        self.port = port
        self.endpoint = endpoint
        self._thread = thread

    def url(self, path):
        assert path.startswith("/")
        return f"http://127.0.0.1:{self.port}{path}"

    def request_count(self):
        response = requests.get(self.url("/request_count"))
        return response.json()["count"]

    def _shutdown(self):
        response = requests.get(self.url("/shutdown"))
        assert "Exiting" in response.text
        self._thread.join()
