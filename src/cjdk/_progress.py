# This file is part of cjdk.
# Copyright 2022-25 Board of Regents of the University of Wisconsin System
# SPDX-License-Identifier: MIT
from __future__ import annotations

import os
import sys
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING, TypeVar, cast

import progressbar

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Sized

_T = TypeVar("_T")

__all__ = [
    "indefinite",
    "data_transfer",
    "iterate",
]


@contextmanager
def indefinite(*, enabled: bool, text: str) -> Iterator[Callable[[], None]]:
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


def data_transfer(
    total_bytes: int | None, iter: Iterable[bytes], *, enabled: bool, text: str
) -> Iterator[bytes]:
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
    max_val: int | type[progressbar.UnknownLength] = (
        total_bytes if total_bytes is not None else progressbar.UnknownLength
    )
    with barclass(max_value=max_val, prefix=f"{text} ") as pbar:
        pbar.start()
        for chunk in iter:
            yield chunk
            size += len(chunk)
            pbar.update(size)


def iterate(
    iter: Iterable[_T], *, enabled: bool, text: str, total: int | None = None
) -> Iterator[_T]:
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
    max_val: int | type[progressbar.UnknownLength]
    if total is not None:
        max_val = total
    elif hasattr(iter, "__len__"):
        max_val = len(cast("Sized", iter))
    else:
        max_val = progressbar.UnknownLength
    bar = barclass(prefix=f"{text} ", max_value=max_val)
    yield from bar(iter)


def _bar_enabled(enabled: bool) -> bool:
    if os.environ.get("CJDK_HIDE_PROGRESS_BARS", "").lower() in (
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
