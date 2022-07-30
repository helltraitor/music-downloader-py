# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains `FileSystemConflict` and `IgnoredException`.

The first one is used for indication what file system must preform when program
attempts to open same track as file (this is fine to open track as track for
setting tags after downloading).

The second one used when the program attempts to open the same track as a file.
That exception means that downloading must be skipped.
"""
from enum import Enum


class FileSystemConflict(Enum):
    """`FileSystemConflict` represents an action when the same file already exists.

    `ERROR` action makes FileSystem to raise a FileExistsError.
        That will make whole application stop.

    `IGNORE` action makes FileSystem to raise a IgnoredException.
        That will allow to continue execution for other tasks.

    `OVERRIDE` makes FileSystem to just override an existed file.
        That will allow to continue execution for all tasks.
    """
    ERROR = 0
    IGNORE = 1
    OVERRIDE = 2


class IgnoredException(Exception):
    """`IgnoredException` exception indicates current file as ignored.

    This exception class must be expected in outer classes (such like `Downloader`).
    """
