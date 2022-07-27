# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains `Descriptor` class that allows to flexible work with tracks.

This class allows using async for both of entities types: files when track saving,
and track when it is editing. Also, this class saves all set id3 tags automatically.

Examples:
    >>> from pathlib import Path
    >>>
    >>> from mutagen import id3
    >>>
    >>> from downloader.filesystem import FileSystem, FileSystemConflict
    >>>
    >>>
    >>> home = FileSystem(FileSystemConflict.OVERRIDE, Path().home())
    >>>
    >>> async with home.into("Downloads") as downloads:
    >>>     async with downloads.open("track.mp3").to_track() as track:
    >>>         track.tags.add(id3.TIT2(encoding=3, text=["SomeTitle"]))
"""
import contextlib
import logging
import io

from collections.abc import AsyncIterator
from pathlib import Path

import aiofiles
import mutagen
import mutagen.id3

from aiofiles.threadpool.binary import AsyncBufferedReader
# Mutagen v1.45.X doesn't allow to use BytesIO or some other file representation
#   This is a bug that has been reported (by author of this application)
# TODO: Wait mutagen update for using bytes buffer instead of private FileThing
from mutagen._util import FileThing


Logger = logging.getLogger(__file__)


class Descriptor:
    """`Descriptor` class is a wrapper around pure os files and mutagen file.

    This class allows using async for both of entities types: files when track
    saving, and track when it is editing.

    Warning:
        Both `to_file` and `to_track` provides context managers which
        ensure that file (or track) was saved properly. For track, it
        means that all tags will be saved after editing. And when no
        id3 tags are set, track files will be saved with en empty id3.

    Examples:
        >>> from pathlib import Path
        >>>
        >>> from mutagen import id3
        >>>
        >>> from downloader.filesystem import FileSystem, FileSystemConflict
        >>>
        >>>
        >>> home = FileSystem(FileSystemConflict.OVERRIDE, Path().home())
        >>>
        >>> async with home.into("Downloads") as downloads:
        >>>     async with downloads.open("track.mp3").to_track() as track:
        >>>         track.tags.add(id3.TIT2(encoding=3, text=["SomeTitle"]))
    """
    def __init__(self, filepath: Path) -> None:
        """Creates a new `Descriptor` for the file in the filepath.

        See class documentation for more information.

        Args:
            filepath: A path to the file that will be opened.
        """
        Logger.debug("Descriptor is created for %s", filepath)
        self.__filepath = filepath

    @contextlib.asynccontextmanager
    async def to_file(self) -> AsyncIterator[AsyncBufferedReader]:
        """Opens a filepath as a file in `wb+` mode in the context.

        This method opens a file concurrently and returns async buffer.
        This buffer can be used for read too, but for this application
        it doesn't matter.

        Examples:
            >>> from pathlib import Path
            >>>
            >>> from downloader.filesystem import FileSystem, FileSystemConflict
            >>>
            >>>
            >>> home = FileSystem(FileSystemConflict.OVERRIDE, Path().home())
            >>>
            >>> async with home.into("Downloads") as downloads:
            >>>     # Descriptor is created in `open` and this method used here
            >>>     async with downloads.open("test.txt").to_file() as file:
            >>>         #                                 ~~~~~~~
            >>>         await file.write(b"Music is cool")

        Yields:
            `AsyncBufferedReader` in the context.
        """
        async with aiofiles.open(self.__filepath, "bw+") as file:
            Logger.debug("Borrow binary file %s", self.__filepath)
            yield file

    @contextlib.asynccontextmanager
    async def to_track(self) -> AsyncIterator[mutagen.FileType]:
        """Reads a content from filepath and creates mutagen `FileType` with ID3 tags.

        Killer feature is a concurrently working with synchronous mutagen package.
        Algorithm is following:
            1. Reads track into bytes buffer
            2. Creates mutagen file
            3. Yields mutagen file
            4. <-- Your code executes here -->
            5. Save mutagen file into bytes buffer
            6. Save buffer into file

        Warning:
            Any changes preformed to the file will be saved. So it's fine to set
            necessary tags and leaving context manager.

        Examples:
            >>> from pathlib import Path
            >>>
            >>> from mutagen import id3
            >>>
            >>> from downloader.filesystem import FileSystem, FileSystemConflict
            >>>
            >>>
            >>> home = FileSystem(FileSystemConflict.OVERRIDE, Path().home())
            >>>
            >>> async with home.into("Downloads") as downloads:
            >>>     async with downloads.open("track.mp3").to_track() as track:
            >>>         track.tags.add(id3.TIT2(encoding=3, text=["SomeTitle"]))

        Yields:
             A mutagen `FileType` that can be used for setting tags.
        """
        async with aiofiles.open(self.__filepath, "br") as file:
            buffer = io.BytesIO(await file.read())

        Logger.debug("Track buffer is prepared from %s", self.__filepath)
        # TODO: Use more proper way to create mutagen file in future versions
        wrapper = FileThing(buffer, self.__filepath.name, self.__filepath.name)
        if (track := mutagen.File(wrapper)) is None:
            Logger.error("Mutagen doesn't recognize format for %s", self.__filepath)
            raise RuntimeError(f"Mutagen unable to recognize format for {self.__filepath}")

        track.tags = track.tags or mutagen.id3.ID3()
        Logger.debug("Borrow binary track %s", self.__filepath)
        try:
            yield track
        finally:
            buffer.seek(0)
            track.save(buffer)
            buffer.seek(0)
            Logger.debug("Track was saved into bytes buffer for %s", self.__filepath)

            async with aiofiles.open(self.__filepath, "bw") as file:
                await file.write(buffer.read())
                Logger.info("Track was saved in %s", self.__filepath)
