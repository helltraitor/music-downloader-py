# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
from __future__ import annotations

import logging
import re

from dataclasses import dataclass, field
from typing import Optional

from aiohttp.client import ClientSession

from downloader.fetcher import Expandable, ExpandedTargets
from downloader.filesystem import FileSystem

from . import api
from .album import Album
from ..options import TrackQuality


Logger = logging.getLogger(__file__)


@dataclass
class Label(Expandable):
    id: str
    albums: list[Album] = field(default_factory=list)
    name: str | None = field(default=None)  # name
    quality: TrackQuality = field(default=TrackQuality.STANDARD, repr=False)

    @staticmethod
    def from_url(url: str) -> Optional[Label]:
        if label := re.search(r"label/(\d*)", url):
            return Label(label.group(1))
        return None

    async def expand(self, session: ClientSession, system: FileSystem) -> list[ExpandedTargets]:
        if self.name is None:
            Logger.error("%s wasn't prepared by `prepare` method", self)
            raise RuntimeError(f"{self} wasn't prepared by `prepare` method")

        async with system.into(self.name) as artist:
            return [ExpandedTargets(artist, self.albums)]

    async def prepare(self, session: ClientSession) -> None:
        request = (api.LABEL_INFO_REQUEST
                      .with_section_fields("params", parameters={"id": self.id}))

        async with request.make(session) as response:
            if response.status != 200:
                Logger.error("Bad response %s for %s", response.status, self)
                raise RuntimeError(f"Bad response {response.status} for {self} with {response.url}")
            meta_info = await response.json()

        self.name = meta_info["label"]["name"]

        for album in meta_info["albums"]:
            self.albums.append(Album(str(album["id"]), quality=self.quality))
