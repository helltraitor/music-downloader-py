# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
from enum import Enum


class TrackQuality(Enum):
    """
    TrackQuality enumeration represents track quality in YandexMusic service.

    HIGH requires user to have premium account with ability to get access to high quality music.
    STANDARD is common and default value for tracks. For full music, user must be registered
        on the service.
    """
    HIGH = 1
    STANDARD = 2

    def hq(self) -> int:
        """
        Converts enumeration variant into hq parameter (see api track meta request).

        Returns:
            int: A valid value for hq parameter according to enumeration variant.
        """
        return 0 if self.value is TrackQuality.STANDARD else 1

    def cover(self) -> str:
        """
        Converts enumeration variant into cover parameter (see api track cover request).

        Returns:
            str: Cover size in `WIDTHxHEIGH` format (400x400 for standard and 1000x1000 for high)
        """
        if self.value is TrackQuality.HIGH:
            return "1000x1000"
        return "400x400"
