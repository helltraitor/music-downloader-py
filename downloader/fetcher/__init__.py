# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This package contains `Fetcher` class and `Target` protocols.

`Fetcher` class is represented the main way to download artists, albums, playlists
and tracks. All these enitites must implement `Expandable` or `Downloadable`
protocol. The first allows to expand artist into albums, and both albums
and playlists into tracks. Each "level" (Artist-Album-Track) can be saved into
separated directory, except tracks for each album: ArtistName/AlbumName/*.mp3

`Target` is consist of `Downloadable` and `Expandable` protocols.
`Downloadable` protocol represents any target that can be downloaded.
`Expandable` protocol represents any target that cannot be downloaded as one.

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
from .fetcher import Fetcher
from .targets import Downloadable, Expandable, Target
