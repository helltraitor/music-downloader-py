# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
import logging

from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

from mutagen import id3, FileType
from pydantic import BaseModel, Field


Logger = logging.getLogger(__file__)


class TrackPosition(BaseModel):
    volume: int  # TPOS
    index: int  # TRCK


class TrackLabel(BaseModel):
    name: str  # TPUB


class TrackAlbum(BaseModel):
    amount: int = Field(alias="trackCount")  # TRCK
    genre: str = Field(default="")  # TCON
    labels: list[TrackLabel]
    position: TrackPosition = Field(alias="trackPosition")
    release: datetime | None = Field(alias="releaseDate", default=None)  # TDRC
    title: str  # TALB
    version: str | None

    def post_init(self):
        if self.version is not None:
            self.title = f"{self.title} ({self.version})"

    def apply(self, file: FileType) -> None:
        if file.tags is None:
            Logger.error("FileType hasn't provided tags. At least empty tags must be set")
            raise RuntimeError("FileType.tags attribute is None, but must be at least an empty instance")

        self.post_init()

        # The chosen one album translates all information in track
        #   I have no guarantee that multiply albums will or nor will exist
        file.tags.add(id3.TRCK(
            encoding=3,  # 3 for UTF-8
            # see mutagen _specs.py

            # Seems like only first value have any meaning
            text=[f"{self.position.index}/{self.amount}"]))

        file.tags.add(id3.TPOS(
            encoding=3,  # 3 for UTF-8
            # see mutagen _specs.py

            text=[self.position.volume]))

        labels = [label.name for label in self.labels]
        file.tags.add(id3.TPUB(
            encoding=3,  # 3 for UTF-8
            # see mutagen _specs.py
            text=["/".join(dict.fromkeys(labels, None).keys())]))

        if self.release is not None:
            file.tags.add(id3.TDRC(
                encoding=3,  # 3 for UTF-8
                # see mutagen _specs.py
                text=[self.release.strftime("%Y-%m-%d %H:%M:%S")]))

        file.tags.add(id3.TALB(
            encoding=3,  # 3 for UTF-8
            # see mutagen _specs.py
            text=[self.title]))


class TrackArtist(BaseModel):
    name: str  # TPE1 (if no composer else) TCOM
    composer: bool


class TrackInfo(BaseModel):
    title: str  # TIT2
    version: str | None
    albums: list[TrackAlbum]
    artists: list[TrackArtist]

    def post_init(self):
        if self.version is not None:
            self.title = f"{self.title} ({self.version})"

    def apply(self, file: FileType) -> None:
        if file.tags is None:
            Logger.error("FileType hasn't provided tags. At least empty tags must be set")
            raise RuntimeError("FileType.tags attribute is None, but must be at least an empty instance")

        self.post_init()

        artists = [artist.name for artist in self.artists if not artist.composer] or [""]
        # All
        file.tags.add(id3.TPE1(
            encoding=3,  # 3 for UTF-8
            # see mutagen _specs.py
            text=["/".join(dict.fromkeys(artists, None).keys())]))
        # Main
        file.tags.add(id3.TPE2(
            encoding=3,  # 3 for UTF-8
            # see mutagen _specs.py
            text=[artists[0]]))

        composers = [artist.name for artist in self.artists if artist.composer]
        file.tags.add(id3.TCOM(
            encoding=3,  # 3 for UTF-8
            # see mutagen _specs.py
            text=["/".join(dict.fromkeys(composers, None).keys())]))

        file.tags.add(id3.TIT2(
            encoding=3,  # 3 for UTF-8
            # see mutagen _specs.py
            text=[self.title]))

        genres = [album.genre for album in self.albums]
        file.tags.add(id3.TCON(
            encoding=3,  # 3 for UTF-8
            # see mutagen _specs.py
            text=["/".join(dict.fromkeys(genres, None).keys())]))

        if self.albums:
            self.albums[0].apply(file)

    def title_from(self, alone: bool) -> str:
        self.post_init()

        if not alone:
            album = self.albums[0]
            # Position with leading zeros
            position = str(album.position.index).rjust(len(str(album.amount)), "0")
            return f"{position}. {self.title}"

        artists = ", ".join({artist.name: None for artist in self.artists}.keys())
        return (artists or "Unknown") + " - " + self.title


class TrackCover(BaseModel):
    content: bytes | None = None  # APIC
    mimetype: str | None = None  # APIC
    resource: str | None = Field(alias="coverUri", default=None)

    def apply(self, file: FileType) -> None:
        """
        Applies APIC tag for file. DOES NOT save file.
        All tags can be found here: https://en.wikipedia.org/wiki/ID3

        Args:
            file: FileType instance that will be applied by APIC tag.
        """
        if self.content is None or self.mimetype is None:
            Logger.warning("Apply was calling for track but no cover provided")
            return

        if file.tags is None:
            Logger.error("FileType hasn't provided tags. At least empty tags must be set")
            raise RuntimeError("FileType.tags attribute is None, but must be at least an empty instance")

        file.tags.add(id3.APIC(
            data=self.content,
            desc="Cover",
            encoding=3,  # 3 for UTF-8
            # see mutagen _specs.py
            mime=self.mimetype,
            # MIME TYPE
            # One of following:
            #     image/jpeg
            #     image/png
            # Maybe other
            # see mutagen _frames.py
            type=3  # 3  for Cover (front)
            # see mutagen _specs.py
        ))


class TrackLyrics(BaseModel):
    authors: str | None = Field(alias="writers", default=None)  # TEXT
    text: str | None = Field(alias="fullLyrics", default=None)  # USLT

    def apply(self, file: FileType) -> None:
        """
        Applies USLT and TEXT (if Lyricist exists) tags for file. DOES NOT save file.
        All tags can be found here: https://en.wikipedia.org/wiki/ID3

        Args:
            file: FileType instance that will be applied by USLT and TEXT tags.
        """
        if self.text is None:
            Logger.warning("Apply was calling for track but no lyrics provided")
            return

        if self.authors is None:
            Logger.warning("Apply was calling for track but no lyrics authors provided")
            return

        if file.tags is None:
            Logger.error("FileType hasn't provided tags. At least empty tags must be set")
            raise RuntimeError("FileType.tags attribute is None, but must be at least an empty instance")

        file.tags.add(id3.TEXT(
            encoding=3,  # 3 for UTF-8
            # see mutagen _specs.py
            text=self.authors.split(", ")))
        file.tags.add(id3.USLT(
            encoding=3,  # 3 for UTF-8
            # see mutagen _specs.py
            text=self.text))


@dataclass
class TrackMeta:
    cover: TrackCover | None = None
    info: TrackInfo | None = None
    lyrics: TrackLyrics | None = None

    def apply(self, file: FileType) -> None:
        """
        Applies all gathered information into file. DOES NOT save file.
        All tags can be found here: https://en.wikipedia.org/wiki/ID3

        Args:
            file: FileType instance that will be filled by tags from this meta.
        """
        if self.cover is not None:
            self.cover.apply(file)

        if self.info is not None:
            self.info.apply(file)

        if self.lyrics is not None:
            self.lyrics.apply(file)


class TrackFile(BaseModel):
    bitrate: int
    codec: str
    filepath: Path | None = None
    resource: str | None = Field(alias="src", default=None)
