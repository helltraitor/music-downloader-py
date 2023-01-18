# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
import logging
import re

from dataclasses import dataclass, field
from typing import Optional, TypeAlias

from aiohttp.client import ClientSession

from downloader.fetcher import Expandable, ExpandedTargets
from downloader.filesystem import FileSystem, IgnoredException

from . import api
from .track import Track
from ..options import TrackQuality


Logger = logging.getLogger(__file__)

Self: TypeAlias = "Playlist"


@dataclass
class Playlist(Expandable):
    user: str
    id: str
    tracks: list[Track] = field(default_factory=list)
    name: str | None = field(default=None)
    available: bool = False
    quality: TrackQuality = field(default=TrackQuality.STANDARD)

    @staticmethod
    def from_url(url: str) -> Optional[Self]:
        """Creates a new instance from its url"""
        if playlist := re.search(r"users/(.*)/playlists/(\d*)", url):
            return Playlist(playlist.group(1), playlist.group(2))
        return None

    async def expand(self, session: ClientSession, system: FileSystem) -> list[ExpandedTargets]:
        if not self.available:
            Logger.warning("Playlist %s is not available", self)

            print("SKIP", self.name or "UNKNOWN")
            raise IgnoredException(f"Playlist {self} is not available")

        if self.name is None:
            Logger.error("%s wasn't prepared by `prepare` method", self)
            raise RuntimeError(f"{self} wasn't prepared by `prepare` method")

        async with system.into(self.name) as playlist:
            return [ExpandedTargets(playlist, self.tracks)]

    async def prepare(self, session: ClientSession) -> None:
        request = (api.PLAYLIST_INFO_REQUEST
                      .with_section_fields("params", parameters={"kinds": self.id, "owner": self.user}))

        async with request.make(session) as response:
            if response.status != 200:
                Logger.error("Bad response %s for %s", response.status, self)
                raise RuntimeError(f"Bad response {response.status} for {self}")
            meta_info = await response.json()

        self.available = meta_info["playlist"]["available"]
        self.name = meta_info["playlist"]["title"]

        for track in meta_info["playlist"]["tracks"]:
            self.tracks.append(Track(str(track["albums"][0]["id"]), str(track["id"]), quality=self.quality))
