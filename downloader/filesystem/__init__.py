# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This package contains `FileSystem` and `Descriptor`.

The first allows using file system as the safe flexible abstraction. `FileSystem`
allows creating folders as a new `FileSystem` in the context (with that folder
as a root) and opening files in `Descriptor`.
The second allows to concurrently open the file as file, or as track. Opening
the file as a track allows setting all necessary tags and save the file on exit
from context manager.

Examples:
    Saving tags concurrentlly without blocking thread via `Descriptor` class.

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
from .core import FileSystemConflict, IgnoredException
from .descriptor import Descriptor
from .filesystem import FileSystem
from .sanitizer import sanitize
