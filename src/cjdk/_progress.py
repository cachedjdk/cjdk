# This file is part of cjdk.
# Copyright 2022 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT

import os
import sys
import time
from contextlib import contextmanager

import progressbar

__all__ = [
    "indefinite",
    "data_transfer",
    "iterate",
]


@contextmanager
def indefinite(*, enabled, text):
    """
    Context manager optionally displaying indefinite progress bar.

    Arguments:
    enabled -- Whether to show progress bar (bool).
    text -- Label text (str).

    The value of the context manager is a callable which should be called every
    iteration with no arguments.
    """
    enabled = _bar_enabled(enabled)
    barclass = progressbar.ProgressBar if enabled else progressbar.NullBar
    with barclass(
        max_value=progressbar.UnknownLength, prefix=f"{text} "
    ) as pbar:
        yield lambda: pbar.update()


def data_transfer(total_bytes, iter, *, enabled, text):
    """
    Wrap bytes iterator with optional progress bar.

    Arguments:
    total_bytes -- Known total (int) or None.
    iter -- Iterator yielding bytes objects.
    enabled -- Whether to show progress bar (bool).
    text -- Label text (str).
    """
    enabled = _bar_enabled(enabled)
    barclass = progressbar.DataTransferBar if enabled else progressbar.NullBar
    size = 0
    if total_bytes is None:
        total_bytes = progressbar.UnknownLength
    with barclass(max_value=total_bytes, prefix=f"{text} ") as pbar:
        pbar.start()
        for chunk in iter:
            yield chunk
            size += len(chunk)
            pbar.update(size)


def iterate(iter, *, enabled, text, total=None):
    """
    Wrap iterator with optional progress bar.

    Arguments:
    iter -- Iterator yielding bytes objects.
    enabled -- Whether to show progress bar (bool).
    text -- Label text (str).
    total -- Known total iteration count (int) or None.
    """
    enabled = _bar_enabled(enabled)
    barclass = progressbar.ProgressBar if enabled else progressbar.NullBar
    if total is None:
        if hasattr(iter, "__len__"):
            total = len(iter)
        else:
            total = progressbar.UnknownLength
    bar = barclass(prefix=f"{text} ", max_value=total)
    yield from bar(iter)


def _bar_enabled(enabled):
    if os.environ.get("CJDK_HIDE_PROGRESS_BARS", "0").lower() in (
        "1",
        "true",
        "yes",
    ):
        return False
    return enabled


# Interactive testing
if __name__ == "__main__":
    mode, enabled = sys.argv[1:]
    enabled = enabled.lower() in ("1", "true")
    COUNT = 30
    if mode == "indefinite":
        with indefinite(enabled=enabled, text="Test") as update_pbar:
            for i in range(COUNT):
                time.sleep(0.1)
                update_pbar()
    elif mode == "iterate":

        def slowiter(n):
            for i in range(n):
                time.sleep(0.1)
                yield i

        for i in iterate(
            slowiter(COUNT), enabled=enabled, text="Test", total=COUNT
        ):
            pass
    elif mode == "data_transfer":
        CHUNKSIZE = 1024

        def slowbyteiter(n):
            for i in range(n):
                time.sleep(0.1)
                yield b"*" * CHUNKSIZE

        for chunk in data_transfer(
            COUNT * CHUNKSIZE,
            slowbyteiter(COUNT),
            enabled=enabled,
            text="Test",
        ):
            pass
    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
