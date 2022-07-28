# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains `Target` protocols that can be used by `Fetcher` class.

Examples:
    >>> from downloader.client import Client
    >>> from downloader.fetcher import Downloadable, Expandable, Fetcher
    >>>
    >>>
    >>> async with Client().create() as client:
    >>>     # Or any other class that implements these protocols
    >>>     await Fetcher(client).fetch(Downloadable())
    >>>     await Fetcher(client).fetch(Expandable())
    >>>
    >>>     # Alternative
    >>>     await Fetcher(client).fetch_all([Downloadable(), Expandable()])
"""
from typing import Protocol, runtime_checkable, TypeAlias, Union

from aiohttp.client import ClientSession

from downloader.filesystem import FileSystem


Target: TypeAlias = Union["Downloadable", "Expandable"]


@runtime_checkable
class Downloadable(Protocol):
    """`Downloadable` protocol represents any target that can be downloaded.

    `Downloadable` protocol user (Fetcher) guarantees that `prepare` method
    will be used before `download`.

    Examples:
        >>> from downloader.client import Client
        >>> from downloader.fetcher import Downloadable, Fetcher
        >>>
        >>>
        >>> async with Client().create() as client:
        >>>     # Or any other class that implements this protocol
        >>>     await Fetcher(client).fetch(Downloadable())
    """
    async def download(self, session: ClientSession, system: FileSystem) -> None:
        """Download method allows downloading target concurrently.

        Moreover, this method allows editing downloaded track via `FileSystem`.
        Session must not be saved in implementation class. That's important
        for active connections' limitation.

        Args:
            session: The `ClientSession` instance that can be used in the internal
                caller methods, but must not be shared anywhere else.
            system: The `FileSystem` instance that must be used for saving file.
                Using `FileSystem` may raise `FileExistsError` and `IgnoredException`,
                which must not be suppressed (caught by using code).
        """

    async def prepare(self, session: ClientSession) -> None:
        """Prepare method allows preparing target before downloading concurrently.

        This method is needed only for target's initialization. Session must
        not be saved in implementation class. That's important for active
        connections' limitation.

        Warning:
            That method must be called first.

        Args:
            session: The `ClientSession` instance that can be used in the internal
                caller methods, but must not be shared anywhere else.
        """


@runtime_checkable
class Expandable(Protocol):
    """`Expandable` protocol represents any target that cannot be downloaded as one.

    `Downloadable` protocol user (Fetcher) guarantees that `prepare` method
    will be used before `download`.

    Examples:
        >>> from downloader.client import Client
        >>> from downloader.fetcher import Expandable, Fetcher
        >>>
        >>>
        >>> async with Client().create() as client:
        >>>     # Or any other class that implements this protocol
        >>>     await Fetcher(client).fetch(Expandable())
    """
    async def expand(self, session: ClientSession, system: FileSystem)\
            -> tuple[FileSystem, list[Target]]:
        """Expand method allows expanding one complicated target into several more simple.

        This method allows artists to expand into albums, and albums and playlists
        into tracks. Expanding chain must be over at tracks by implementing
        `Downloadable` protocol for the last.

        Examples:
            Example of returning a new `FileSystem`.

            >>> from downloader.fetcher import Expandable
            >>>
            >>>
            >>> class Artist(Expandable):
            >>>     def __init__(self, id: str) -> None:
            >>>         self.id = id
            >>>         self.name: str | None = None
            >>>
            >>>     async def expand(self, session: ClientSession, system: FileSystem)\
            >>>             -> tuple[FileSystem, list[Target]]:
            >>>         if self.name is None:
            >>>             raise RuntimeError("Prepare method was not called")
            >>>
            >>>         # Making request and collect all targets
            >>>         targets = []
            >>>         async with system.into(self.name) as subsystem:
            >>>             return subsystem, targets

        Args:
            session: The `ClientSession` instance that can be used in the internal
                caller methods, but must not be shared anywhere else.
            system: The `FileSystem` instance that must be used for saving file.
                Using `FileSystem` may raise `FileExistsError` and `IgnoredException`,
                which must not be suppressed (caught by using code).

        Returns:
            The tuple of `FileSystem` and list of `Target`. The first one allows
            changing working directory. The second one is about targets that
            will be saved in the `FileSystem` root.
        """

    async def prepare(self, session: ClientSession) -> None:
        """Prepare method allows preparing target before expanding concurrently.

        This method is needed only for target's initialization. Session must
        not be saved in implementation class. That's important for active
        connections' limitation.

        Warning:
            That method must be called first.

        Args:
            session: The `ClientSession` instance that can be used in the internal
                caller methods, but must not be shared anywhere else.
        """
