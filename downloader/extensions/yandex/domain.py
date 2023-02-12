# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
import re
import logging

from downloader.fetcher import Target
from downloader.domains import Domain, Fetchable

from .models import Album, Artist, Label, Playlist, Track
from .options import TrackQuality


Logger = logging.getLogger(__file__)

# ORDER IS IMPORTANT: Track < Album
FETCH_MODELS = [Track, Album, Playlist, Artist, Label]

HOST_PATTERN = re.compile(r"((http(s)?://)?music\.yandex\.(by|kz|ru|ua))")


class Yandex(Domain, Fetchable):
    """This domain represents `yandex.ru` v1.0.0

    This domain supports urls from following sources:
    Track, Album, Artist, Playlist, Label

    This domain requires `Session_id` cookie from `yandex.ru` site (it can be
    found in application tab in development tools of user browser).

    Supported options:
        HQ, HighQuality - Forces to use a high quality tracks and covers.
                          In case if user have no plus subscribing, may entail
                          errors.

    Use flag `-o` (or `--option`) for enabling a specified option.

    Examples:
        | downloader fetch <url> -d %USERPROFILE%/Downloads -o HighQuality
    """
    def __init__(self) -> None:
        self.quality = TrackQuality.STANDARD

    @staticmethod
    def match(url: str) -> bool:
        return bool(re.match(HOST_PATTERN, url))

    def activate(self, common_options: list[str], kwargs_options: dict[str, str]) -> None:
        for option in common_options:
            match option:
                case "HQ" | "HighQuality":
                    self.quality = TrackQuality.HIGH
                case _:
                    Logger.warning("Option %s is not supported by Yandex domain", option)

    def fetch_from(self, url: str) -> Target:
        for item in FETCH_MODELS:
            if (target := item.from_url(url)) is None:
                continue

            target.quality = self.quality
            return target

        Logger.error("Yandex domain unable to recognize url: %s", url)
        raise ValueError(f"Unable to recognize url {url}")
