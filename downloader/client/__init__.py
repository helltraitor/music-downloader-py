# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This package contains Client implementation with cookie keep support.

`Client` class must be the only one way to make requests to the servers. This
class limit active connection by its limit count and allow to save set cookies
in the file system via `CookiesStorage`.

`CookiesStorage` is the common cookies' storage for all clients and their sessions.
By default, `downloader/cookies/` folder is using, but `CookiesStorage` allows
to change it on creation. This class allows to keep cookies in the filesystem,
load, save, update and delete each one.

Note: `CookiesStorage` work by synchronize principal, so cookies must be updated
via `Client` and only then saved. Otherwise, cookie will be replaced by a new one.

Examples:
    Using both Client and CookieStorage

    >>> import asyncio
    >>>
    >>> from downloader.client import Client, CookiesStorage
    >>>
    >>>
    >>> def task(client: Client) -> None:
    >>>     async with client.session() as session:
    >>>         pass  # Do something
    >>>
    >>>
    >>> storage = CookiesStorage()
    >>>
    >>> async with Client(storage=storage).create() as client:
    >>>     # For created 100 tasks, only 4 (by limit default)
    >>>     #   can use session object in the same time
    >>>     await asyncio.gather(*(task(client) for _ in range(100)))
"""
from .client import Client, RateLimit
from .cookies import CookiesStorage
