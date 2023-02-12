# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains `sanitize` function that allows to sanitize any name for os.

Tries to sanitize name and returns a valid representation if all os. In case
if name cannot be sanitized, returns a md5 hexdigit of name via `hashlib`.

Warning:
    This function depends on `pathvalidate` package.
    See `pathvalidate.sanitize_filename` for more information.

Examples:
    >>> from downloader.filesystem import sanitize
    >>>
    >>>
    >>> assert sanitize("/coolname!/", "_") == "_coolname!_"
"""
import hashlib
import logging

from pathvalidate import sanitize_filename


Logger = logging.getLogger(__file__)


def sanitize(name: str, displace: str) -> str:
    """Sanitizes a name and makes it more reliable for os file system.

    This function can't provide any guarantees, because depends on `pathvalidate`
    package. This function must be used for sanitizing all names (directories and
    files). In case if name cannot be sanitized, returns a md5 hexdigit of name
    via `hashlib`.

    Args:
        name: A name that will be sanitized.
        displace: String that will be used as replacement for invalid characters.

    Returns:
        str: A valid name or md5 hexdigit in case when name is invalid.

    Raises:
            ValueError: When displace doesn't pass sanitize check `sanitize(displace) != displace`
    """
    if sanitize_filename(displace) != displace:
        Logger.error("Invalid displace provided %s", displace)
        raise ValueError(f"Invalid displace provided `{displace}`")

    try:
        sanitized = sanitize_filename(name,
                                      check_reserved=True,
                                      replacement_text=displace)
    except ValueError as exc:
        Logger.error("Unable to sanitize filename `%s`", name, exc_info=exc)
        return hashlib.md5(name.encode("utf-8")).hexdigest()
    return str(sanitized).strip()
