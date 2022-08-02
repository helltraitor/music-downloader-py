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

Self: TypeAlias = "Album"


@dataclass
class Album(Expandable):
    id: str
    volumes: list[list[Track]] = field(default_factory=list)
    title: str | None = field(default=None)
    alone: bool = True
    available: bool = False
    quality: TrackQuality = field(default=TrackQuality.STANDARD, repr=False)

    @staticmethod
    def from_url(url: str) -> Optional[Self]:
        """Creates a new instance from its url"""
        if album := re.search(r"album/(\d*)", url):
            return Album(album.group(1))
        return None

    async def expand(self, session: ClientSession, system: FileSystem) -> list[ExpandedTargets]:
        if not self.available:
            Logger.warning("Album %s is not available", self)

            print("SKIP", self.title or "UNKNOWN")
            raise IgnoredException(f"Album {self} is not available")

        if self.title is None:
            Logger.error("%s wasn't prepared by `prepare` method", self)
            raise RuntimeError(f"{self} wasn't prepared by `prepare` method")

        expanded = []
        async with system.into(self.title) as album:
            if len(self.volumes) == 1:
                return [ExpandedTargets(album, self.volumes[0])]

            for part, tracks in enumerate(self.volumes, 1):
                async with album.into(f"CD{part}") as subdir:
                    expanded.append(ExpandedTargets(subdir, tracks))
        return expanded

    async def prepare(self, session: ClientSession) -> None:
        request = (api.ALBUM_INFO_REQUEST
                      .with_section_fields("params", parameters={"album": self.id}))

        async with request.make(session) as response:
            if response.status != 200:
                Logger.error("Bad response %s for %s", response.status, self)
                raise RuntimeError(f"Bad response {response.status} for {self}")
            meta_info = await response.json()

        self.available = meta_info["available"]

        self.title = meta_info["title"]
        if "version" in meta_info:
            self.title = f"{self.title} ({meta_info['version']})"

        if self.alone:
            artists = ", ".join((artist["name"] for artist in meta_info["artists"]))
            self.title = artists + " - " + self.title  # type: ignore

        for index, volume in enumerate(meta_info["volumes"]):
            self.volumes.append([Track(self.id, track["id"], alone=False, quality=self.quality)
                                 for track in volume])
