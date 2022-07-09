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

    The value of the context manager is the progress bar, which has method
    update(), which should be called every iteration with no arguments.
    """
    enabled, faked = _bar_mode(enabled)
    barclass = progressbar.ProgressBar if enabled else progressbar.NullBar
    with barclass(
        max_value=progressbar.UnknownLength, prefix=f"{text} "
    ) as pbar:
        pbar.start()

        class PBar:
            def update(self):
                if not faked:
                    pbar.update()

        yield PBar()


def data_transfer(total_bytes, iter, *, enabled, text):
    """
    Wrap bytes iterator with optional progress bar.

    Arguments:
    total_bytes -- Known total (int) or None.
    iter -- Iterator yielding bytes objects.
    enabled -- Whether to show progress bar (bool).
    text -- Label text (str).
    """
    enabled, faked = _bar_mode(enabled)
    barclass = progressbar.DataTransferBar if enabled else progressbar.NullBar
    size = 0
    if total_bytes is None:
        total_bytes = progressbar.UnknownLength
    with barclass(max_value=total_bytes, prefix=f"{text} ") as pbar:
        pbar.start()
        for chunk in iter:
            yield chunk
            size += len(chunk)
            if not faked:
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
    enabled, faked = _bar_mode(enabled)
    barclass = progressbar.ProgressBar if enabled else progressbar.NullBar
    if total is None:
        if hasattr(iter, "__len__"):
            total = len(iter)
        else:
            total = progressbar.UnknownLength
    bar = barclass(prefix=f"{text} ", max_value=total)
    if faked:
        with bar as pbar:
            pbar.start()
            yield from iter
    else:
        yield from bar(iter)


def _bar_mode(enabled):
    mode = os.environ.get("CJDK_OVERRIDE_PROGRESS_BARS", "no").lower()
    if mode == "no":
        return enabled, False
    elif mode == "hide":
        return False, False
    elif mode == "fake":
        return enabled, True


# Interactive testing
if __name__ == "__main__":
    mode, enabled = sys.argv[1:]
    enabled = enabled.lower() in ("1", "true")
    COUNT = 30
    if mode == "indefinite":
        with indefinite(enabled=enabled, text="Test") as pbar:
            for i in range(COUNT):
                time.sleep(0.1)
                pbar.update()
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
