# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains `Fetcher` class that must be used for downloading `Targets`.

`Fetcher` class is represented the main way to download artists, albums, playlists
and tracks. All these enitites must implement `Expandable` or `Downloadable`
protocol. The first allows to expand artist into albums, and both albums
and playlists into tracks. Each "level" (Artist-Album-Track) can be saved into
separated directory, except tracks for each album: ArtistName/AlbumName/*.mp3

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
import asyncio
import logging

from collections.abc import Sequence

from downloader.client import Client
from downloader.filesystem import FileSystem, IgnoredException

from .targets import Downloadable, Expandable, Target


Logger = logging.getLogger(__file__)


class Fetcher:
    """`Fetcher` class allows downloading both tracks and more complicated entities.

    This class provides methods for downloading `Targets` and saving them into
    filesystem. `Fetcher` guarantees that `prepare` method will be called first.

    Examples:
        >>> from downloader.client import Client
        >>> from downloader.fetcher import Fetcher, Downloadable
        >>>
        >>>
        >>> async with Client().create() as client:
        >>>     # Or any other class that implements this protocol
        >>>     await Fetcher(client).fetch(Downloadable())
    """
    def __init__(self, client: Client) -> None:
        """Creates a new `Fetcher` instance.

        See class documentation for more information.

        Args:
            client: The `Client` instance that will be used for fetching.
        """
        self.__client = client

    async def fetch(self, target: Target, system: FileSystem) -> None:
        """Fetch method uses `Target` protocols for expanding and downloading.

        Fetch method expands all `Expandable` targets until reaches `Downloadable`.
        All happens concurrently and according to client limit for active connections.
        The recursion depth of expandable items doesn't matter.

        Examples:
        >>> from downloader.client import Client
        >>> from downloader.fetcher import Fetcher, Downloadable
        >>>
        >>>
        >>> async with Client().create() as client:
        >>>     # Or any other class that implements this protocol
        >>>     await Fetcher(client).fetch(Downloadable())

        Args:
            target: Any object that implements one of `Target` protocols.
            system: The `FileSystem` instance that will be used for saving files.
                Each `Expandable` can change working directory into more nested.
        """
        Logger.info("Target %s will be saved in %s", target, system.root)
        async with self.__client.session() as session:
            await target.prepare(session)

        Logger.info("Target %s was successfully prepared", target)

        if isinstance(target, Expandable):
            async with self.__client.session() as session:
                try:
                    expanded = await target.expand(session, system)
                except IgnoredException:
                    Logger.info("Expandable target %s is ignored", target)
                    return

            Logger.info("Expandable target %s was successfully expanded", target)
            tasks = [self.fetch_all(group.targets, group.root) for group in expanded]
            await asyncio.gather(*tasks)

        elif isinstance(target, Downloadable):
            try:
                async with self.__client.session() as session:
                    await target.download(session, system)
            except IgnoredException:
                Logger.info("Downloadable target %s is ignored", target)
            else:
                Logger.info("Downloadable target %s was successfully downloaded", target)

    async def fetch_all(self, targets: Sequence[Target], system: FileSystem) -> None:
        """Fetches all targets concurrently via `fetch` method.

        See `fetch` method for more information.

        Examples:
        >>> from downloader.client import Client
        >>> from downloader.fetcher import Fetcher, Downloadable, Expandable
        >>>
        >>>
        >>> targets = [Expandable(), Downloadable()]
        >>>
        >>> async with Client().create() as client:
        >>>     # Or any other list of classes which implements this protocol
        >>>     await Fetcher(client).fetch_all(targets)

        Args:
            targets: List of any objects that implements one of `Target` protocols.
            system: The `FileSystem` instance that will be used for saving files.
                Each `Expandable` can change working directory into more nested.
        """
        Logger.info("Targets %s will be saved in %s", targets, system.root)
        await asyncio.gather(*(self.fetch(target, system) for target in targets))
