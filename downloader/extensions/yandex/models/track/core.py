# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
import hashlib
import logging
import re

from dataclasses import dataclass, field
from typing import TypeAlias, Optional

from aiohttp import ClientSession
from defusedxml import ElementTree

from downloader.fetcher import Downloadable
from downloader.filesystem import FileSystem, IgnoredException

from .models import TrackFile, TrackMeta, TrackCover, TrackInfo, TrackLyrics
from .. import api
from ...options import TrackQuality


Logger = logging.getLogger(__file__)


# TODO: Alias to Self from Python 3.11
Self: TypeAlias = "Track"


@dataclass
class Track(Downloadable):
    album: str
    id: str
    file: TrackFile | None = field(default=None, repr=False)
    meta: TrackMeta | None = field(default=None, repr=False)
    available: bool = False
    alone: bool = False
    quality: TrackQuality = field(default=TrackQuality.STANDARD, repr=False)

    @staticmethod
    def from_url(url: str) -> Optional[Self]:
        """Creates a new instance from its url"""
        if track := re.search(r"album/(\d*)/track/(\d*)", url):
            return Track(track.group(1), track.group(2))
        return None

    async def download(self, session: ClientSession, system: FileSystem) -> None:
        if not self.available:
            Logger.warning("Track %s is not available", self)

            # Track must be prepared at this stage
            print("SKIP", self.meta.info.title)  # type: ignore
            raise IgnoredException(f"Track {self} is not available")

        if not all((self.file, self.meta, self.meta)):
            Logger.error("%s wasn't prepared by `prepare` method", self)
            raise RuntimeError(f"{self} wasn't prepared by `prepare` method")

        # Receiving and processing download info
        src = self.file.resource.removeprefix("//")
        request = (api.TRACK_DOWN_REQUEST
                      .with_url_fields(parameters={"src": src}))

        async with request.make(session) as response:
            if response.status != 200:
                Logger.error("Bad response %s for %s", response.status, self)
                raise RuntimeError(f"Bad response {response.status} for {self}")
            xml_content = await response.text()

        download_info = ElementTree.fromstring(xml_content, forbid_dtd=True)

        url: str = download_info.find("path").text.removeprefix("/")
        # Special source string that will be used only once in md5 hash
        source = "XGRlBW9FXlekgbPrRHuSiA" + url + download_info.find("s").text
        hashed = hashlib.md5(source.encode()).hexdigest()

        # Downloading file
        request = (api.TRACK_FILE_REQUEST
                      .with_url_fields(parameters={
                          "host": download_info.find("host").text,
                          "ts": download_info.find("ts").text,
                          "hash": hashed,
                          "path": url})
                      .with_section_fields("params", parameters={
                          "track-id": self.id}))

        title = self.meta.info.title_from(self.alone)
        filename = title + "." + self.file.codec

        # Trying to open file before downloading, because file may exist
        #  In that case IgnoredException or FileExistError occurs
        async with system.open(filename).to_file() as file:
            async with request.make(session) as response:
                if response.status != 200:
                    Logger.error("Bad response %s for %s", response.status, self)
                    raise RuntimeError(f"Bad response {response.status} for {self}")

                Logger.info("Begin downloading track %s", title)
                # TODO: Progress bar via iter_chunks
                content = await response.read()
                await file.write(content)
        Logger.info("Track %s was successfully downloaded", title)

        # TODO: Replace with click or something else
        print("DONE", title)

        Logger.info("Begin applying tags for track %s", title)
        async with system.open(filename).to_track() as track:
            self.meta.apply(track)

    async def prepare(self, session: ClientSession) -> None:
        # Both under must have been prepared in following order:
        await self.prepare_meta(session)
        await self.prepare_cover(session)
        # After all
        await self.prepare_file(session)

        Logger.info("Preparing %s complete", self)

    async def prepare_cover(self, session: ClientSession) -> None:
        """Downloads cover and keeps it until main downloading phase.

        Args:
            session: The client session instance that will be used for making requests.
        """
        if not all((self.meta, self.meta.cover)):
            Logger.error("%s wasn't prepared by `prepare_meta` method", self)
            raise RuntimeError(f"{self} wasn't prepared by `prepare_meta` method")

        src = self.meta.cover.resource.replace("%%", self.quality.cover())
        request = (api.TRACK_COVER_REQUEST
                      .with_url_fields(parameters={"src": src}))

        async with request.make(session) as response:
            if response.status != 200:
                Logger.error("Bad response %s for %s", response.status, self)
                raise RuntimeError(f"Bad response {response.status} for {self}")

            if "CONTENT-TYPE" not in response.headers:
                Logger.error("Content type is unset for %s", self)
                raise RuntimeError("Content type is not set in headers")

            # According to RFC2616
            if response.headers["CONTENT-TYPE"] == "application/octet-stream":
                Logger.error("Bad content type `application/octet-stream` (RFC2616) for %s", self)
                raise RuntimeError("Bad content type `application/octet-stream` (RFC2616)")

            self.meta.cover.content = await response.read()
            self.meta.cover.mimetype = response.headers["CONTENT-TYPE"]
        Logger.info("Cover was successfully prepared for %s", self)

    async def prepare_file(self, session: ClientSession) -> None:
        """Downloads necessary information that will be used on downloading track phase.

        Must be called after `prepare_meta`.

        Args:
            session: The client session instance that will be used for making requests.
        """
        if not self.available:
            # Download method tells about available state
            Logger.warning("Unable to receive file information for %s", self)
            return

        request = (api.TRACK_META_REQUEST
                      .with_url_fields(parameters={"album": self.album, "track": self.id})
                      .with_section_fields("params", parameters={"hq": self.quality.hq()}))

        async with request.make(session) as response:
            if response.status != 200:
                Logger.error("Bad response %s for %s", response.status, self)
                raise RuntimeError(f"Bad response {response.status} for {self}")
            self.file = TrackFile.parse_obj(await response.json())
        Logger.info("File was successfully prepared for %s", self)

    async def prepare_meta(self, session: ClientSession) -> None:
        """Downloads all necessary track information (title, album title and so on).

        Args:
            session: The client session instance that will be used for making requests.
        """
        request = (api.TRACK_INFO_REQUEST
                      .with_section_fields("params", parameters={"track": self.id}))
        async with request.make(session) as response:
            if response.status != 200:
                Logger.error("Bad response %s for %s", response.status, self)
                raise RuntimeError(f"Bad response {response.status} for {self}")
            full_info = await response.json()

        self.available = full_info["track"]["available"]
        self.meta = TrackMeta(cover=TrackCover.parse_obj(full_info["track"]),
                              info=TrackInfo.parse_obj(full_info["track"]))

        if full_info.get("lyricsAvailable"):
            self.meta.lyrics = TrackLyrics.parse_obj(full_info["lyric"][0])
