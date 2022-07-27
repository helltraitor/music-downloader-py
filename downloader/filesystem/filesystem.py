# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains `IgnoredException`, `FileSystemConflict` and `FileSystem`.

The main class is a `FileSystem`. That class allows using os file system
safely, without afraid to harm file system (by bad naming). All names are
sanitized by `sanitize` function from `sanitizer` module.

Examples:
    >>> from pathlib import Path
    >>>
    >>> from downloader.filesystem import FileSystem, FileSystemConflict
    >>>
    >>>
    >>> home = FileSystem(FileSystemConflict.OVERRIDE, Path().home())
    >>>
    >>> async with home.into("Downloads") as downloads:
    >>>     async with downloads.open("test.txt").to_file() as file:
    >>>         await file.write(b"Music is cool")
"""
import contextlib
import logging

from collections.abc import AsyncIterator
from enum import Enum
from pathlib import Path
from typing import TypeAlias

from .descriptor import Descriptor
from .sanitizer import sanitize


Logger = logging.getLogger(__file__)

Self: TypeAlias = "FileSystem"


class IgnoredException(Exception):
    """`IgnoredException` exception indicates current file as ignored.

    This exception class must be expected in outer classes (such like `Downloader`).
    """


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


class FileSystem:
    """`FileSystem` class is the more preferred way to interact with the os file system.

    This class allows to create folder with a filesystem in context. Further,
    that new instance can be used in child classes of expanded item (artist
    folder can be used as a root for album and so on in separated contexts).

    Also, this class allows controlling what happened when the same file
    (not folder) already exist. For example, on update this class allows
    to skip all existed tracks and add only new one.

    Examples:
        The same files can be ignored by catching a special exception: `IgnoredExcpetion`.
        That makes control flow to go upper from called code (it doesn't necessary
        to continue execution in a function that saves track when it already exists,
        so this only one way to return to outer code and continue work).

        >>> from pathlib import Path
        >>>
        >>> import aiofiles
        >>>
        >>> from downloader.filesystem import FileSystem, FileSystemConflict
        >>>
        >>>
        >>> downloads = Path().home() / "Downloads"
        >>>
        >>> files = FileSystem(FileSystemConflict.IGNORE, downloads)
        >>>
        >>> async with aiofiles.open(downloads / "test.txt", "wb") as file:
        >>>     await file.write(b"Music is cool")
        >>>
        >>> async with files.open("test.txt").to_file() as file:
        >>>     # This exception must be expected at called code
        >>>     pass  # Unreachable, IgnoredException occurred
    """
    def __init__(self, conflict: FileSystemConflict, root: Path) -> None:
        """Creates a new `FileSystem` instance.

        See class documentation for more information.

        Args:
            conflict: Action, when the same file already exists.
            root: The working directory of the filesystem.
        """
        self.__conflict = conflict
        self.__root = root

    @property
    def root(self) -> Path:
        """Returns current root of filesystem.

        That root represents a working directory.

        Returns:
            Current root of file system.
        """
        return self.__root

    @contextlib.asynccontextmanager
    async def into(self, dirname: str) -> AsyncIterator[Self]:
        """Creates a new folder in the root and returns a new `FileSystem` it in context.

        Creates a new folder and created a new instance with this directory
        as the root. That allows to recursively expand artists into albums
        and albums into tracks in separated context.

        Examples:
            >>> from pathlib import Path
            >>>
            >>> from downloader.filesystem import FileSystem, FileSystemConflict
            >>>
            >>>
            >>> files = FileSystem(FileSystemConflict.IGNORE, Path().home())
            >>>
            >>> async with files.into("Downloads") as downloads:
            >>>     async with files.into("Music") as music:
            >>>         pass  # Do something in this folder

        Args:
            dirname: A directory name that will be automatically sanitized.

        Yields:
            A new `FileSystem` instance in specified dir as the root dir.
        """
        # SAFE: This is a mypy bug
        yield FileSystem(self.__conflict, self.__root / sanitize(dirname))  # type: ignore

    def open(self, filename: str) -> Descriptor:
        """Returns a new `Descriptor` if no file exists otherwise raises exceptions.

        Action, when the same file already exists, depends on `FileSystemConflict`.
        See `FileSystemConflict` for more information or the examples.

        Examples:
            Error on the same file when error on conflicts

            >>> from pathlib import Path
            >>>
            >>> import aiofiles
            >>>
            >>> from downloader.filesystem import FileSystem, FileSystemConflict
            >>>
            >>>
            >>> downloads = Path().home() / "Downloads"
            >>>
            >>> files = FileSystem(FileSystemConflict.ERROR, downloads)
            >>>
            >>> async with aiofiles.open(downloads / "test.txt", "wb") as file:
            >>>     await file.write(b"Music is cool")
            >>>
            >>> async with files.open("test.txt").to_file() as file:
            >>>     pass  # Unreachable, FileExistsError occurred

            `IgnoredException` on the same file when ignored on conflicts

            >>> from pathlib import Path
            >>>
            >>> import aiofiles
            >>>
            >>> from downloader.filesystem import FileSystem, FileSystemConflict
            >>>
            >>>
            >>> downloads = Path().home() / "Downloads"
            >>>
            >>> files = FileSystem(FileSystemConflict.IGNORE, downloads)
            >>>
            >>> async with aiofiles.open(downloads / "test.txt", "wb") as file:
            >>>     await file.write(b"Music is cool")
            >>>
            >>> async with files.open("test.txt").to_file() as file:
            >>>     # This exception must be expected at called code
            >>>     pass  # Unreachable, IgnoredException occurred

            Overriding on the same file when ignored on conflicts

            >>> from pathlib import Path
            >>>
            >>> import aiofiles
            >>>
            >>> from downloader.filesystem import FileSystem, FileSystemConflict
            >>>
            >>>
            >>> downloads = Path().home() / "Downloads"
            >>>
            >>> files = FileSystem(FileSystemConflict.OVERRIDE, downloads)
            >>>
            >>> async with aiofiles.open(downloads / "test.txt", "wb") as file:
            >>>     await file.write(b"Music is cool")
            >>>
            >>> async with files.open("test.txt").to_file() as file:
            >>>     await file.write(b"Music is not cool")  # :D

        Args:
            filename: The name of file that will be sanitized and used in `Descriptor`.

        Returns:
            A new `Descriptor` that allows to use a file as file or track.
        """
        filepath = self.__root / sanitize(filename)
        Logger.debug("Trying to open file at %s", filepath)
        if filepath.exists():
            if self.__conflict is FileSystemConflict.ERROR:
                Logger.error("File already exists at %s", filepath)
                raise FileExistsError(f"File already exists at {filepath}")

            if self.__conflict is FileSystemConflict.IGNORE:
                Logger.info("Ignoring file at %s", filepath)
                raise IgnoredException(f"File ignored at {filepath}")
        return Descriptor(filepath)
