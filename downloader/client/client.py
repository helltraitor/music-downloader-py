# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains safe `Client` wrapper around `ClientSession`.

`Client` class role is to limit connection by maximum allowed and to keep
set cookies (via `CookiesStorage`). By default, only 4 tasks can use session.
Of course, here is no protection from using the session outside the `with`
block but this is relaying on code users.

Examples:
    Typical using example

    >>> import asyncio
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

    Keeping cookies example

    >>> storage = CookiesStorage()
    >>>
    >>> async with Client(storage=storage).create() as client:
    >>>     async with client.session() as session:
    >>>         async with session.get("example.com") as response:
    >>>             pass  # Do something
    >>>
    >>>    async with client.session() as session:
    >>>         pass  # Here is the same cookies as in the previous session
    >>>
    >>>
    >>> storage = CookiesStorage()
    >>>
    >>> async with Client(storage=storage).create() as client:
    >>>     async with client.session() as _session:
    >>>         pass  # Same cookies, because these were saved
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
import typing

from collections.abc import AsyncIterator
from http.cookies import SimpleCookie
from typing import Literal

from aiohttp.client import ClientSession
from yarl import URL

from .cookies import CookiesStorage


Logger = logging.getLogger(__file__)

RateLimit = Literal[1, 2, 3, 4, 5, 6, 7, 8]


class Client:
    """Client is the wrapping around ClientSession with usage limit.

    Client class is allowed to share between async tasks. In the same time,
    client load and save cookies from CookieStorage, and also makes sure that
    ClientSession will close correctly.

    Examples:
        Example of typical using

        >>> import aiofiles
        >>>
        >>>
        >>> storage = CookiesStorage()
        >>>
        >>> async with Client(storage=storage).create() as client:
        >>>     async with client.session() as session:
        >>>         async with session.get("example.com") as response:
        >>>             content = response.read()
        >>>
        >>> async with aiofiles.open("example.html", mode="w") as file:
        >>>     await file.write(content)
    """
    def __init__(self,
                 *,
                 cookies: dict[str, str] | None = None,
                 storage: CookiesStorage | None = None,
                 limit: RateLimit = 4) -> None:
        """Creates a new Client (that is wrapper around ClientSession).

        Args:
            cookies: Default cookies that will be applied to a new client.
                These cookies will also save in storage.
            storage: CookiesStorage instance in case if Client need to save
                collected cookies. No cookies saved when CookiesStorage is not
                provided.
            limit: The limitation of active connection. See RateLimit Literal
                for possible values. If value is not in literal, then ValueError
                will raise.

        Raises:
            ValueError: When limit is out of Literal bounds.
        """
        self.__cookies: dict[str, str] = cookies or {}
        self.__storage = storage
        self.__limit = limit
        self.__amount = 0
        self.__session: ClientSession | None = None

        if limit not in typing.get_args(RateLimit):
            Logger.error("Client rate limit %s is out of bounds %s ", limit, RateLimit)
            raise ValueError(f"Value {limit} is out of bounds {RateLimit}")

    def cookies(self) -> dict[str, SimpleCookie]:
        """Returns all cookies from current session.

        Returns all cookies from `ClientSession.cookiejar._cookies`. This
        field is non-public so there is no guarantee that it will work in
        the future versions.

        Examples:
            >>> async with Client().create() as client:
            >>>     # Do some requests...
            >>>     print(client.cookies())  # Display all cookies

        Returns:
            Mapping of domains and its SimpleCookie objects.

        Raises:
            AttributeError: Possible raise in future version:
                The `_cookies` field is protected in CookieJar
            RuntimeError: When client (ClientSession) wasn't created by
                `create` context manager.
        """
        if self.__session is None:
            Logger.error("Unable to get cookies for unset session")
            raise RuntimeError("ClientSession was not created")

        # UNSAFE: _cookie is a protected field that may not exist in the future
        # REASON: This is the only way to access all cookies.
        return getattr(self.__session.cookie_jar, "_cookies")

    @contextlib.asynccontextmanager
    async def create(self) -> AsyncIterator[Client]:
        """Creates a ClientSession instance in context and returns self.

        Creating ClientSession in context manager allows to safely shutdown
        in case of errors, also it allows to save cookies into CookiesStorage
        (loading can be implemented without context manager but not saving cannot).

        Examples:
            Example without CookiesStorage

            >>> async with Client().create() as _client:
            >>>    # Do some requests...
            >>>
            >>> # Cookies were not saved

             Example with CookiesStorage

            >>> storage = CookiesStorage()
            >>>
            >>> async with Client(storage=storage).create() as client:
            >>>     # Do some requests...
            >>>
            >>> async with Client(storage=storage).create() as _client:
            >>>     # Do some other requests but with the same cookies

        Yields:
            Client: The self instance for further using with guarantee that
                session will close in any case.

        Raises:
            RuntimeError: If amount is different from zero.
                Note: In case of this error, session will close any way.
        """
        self.__session = ClientSession(cookies=self.__cookies)

        # load cookies is storage is provided
        if self.__storage is not None:
            await self.__storage.load()
            for domain, cookie in self.__storage.domains().items():
                Logger.debug("Set domain %s with cookie %s", domain, cookie)
                self.__session.cookie_jar.update_cookies(cookie, URL(domain))

        Logger.info("ClientSession is successfully created")
        try:
            yield self
        finally:
            await self.__session.close()
            # Waiting for client closing due to asyncio working principals
            await asyncio.sleep(0.250)

            # save cookies if storage is provided
            if self.__storage is not None:
                await self.__storage.update(self.cookies())

            self.__session = None

            # In situation when amount is not equals to zero, some code logic
            #   is wrong, so this code makes critical log
            if self.__amount > 0:
                message = ("ClientSession was closed while using in %s tasks. "
                           "This is a critical issue and means that code "
                           "logic is broken. Please, pay attention to this")
                Logger.critical(message, self.__amount)
                raise RuntimeError(f"Closed while using in {self.__amount} tasks")
            Logger.info("ClientSession is successfully closed")

    @contextlib.asynccontextmanager
    async def session(self,
                      *,
                      sleep_seconds: float = 0.1,
                      timeout_seconds: float | None = None) -> AsyncIterator[ClientSession]:
        """Returns a ClientSession instance in context.

        Returning the ClientSession in context manager allows to safely count
        the amount of using and safely change amount value no matter of the
        occurred errors.

        Returns the ClientSession instance if amount of using is less than limit,
        otherwise async sleep `sleep_seconds` seconds, checks if `timeout_seconds`
        expired and then tries again.

        Note: `session` method increase amount of session using (that cannot be more
        than client limit). So make sure that session is not used in several places
        of one async task at one time. That may make task wait for session forever.

        Examples:
            >>> # Example without CookiesStorage
            >>> async with Client(limit=1).create() as client:
            >>>    async with client.session() as session:
            >>>        async with client.session() as duplicate:
            >>>            # STUCK FOREVER

        Args:
            sleep_seconds: Seconds amount that method will wait until next
                try to access the session.
            timeout_seconds: Timeout in seconds after that TimeoutError
                will be raised. Default is None that means try until
                get the session.

        Yields:
            ClientSession: The session instance as the context manager that
                allows to safely control usage amount. If using amount is
                less than limit then session yields immediately, otherwise
                awaits sleep_seconds time until timeout_seconds happen.

        Raises:
            TimeoutError: If timeout_seconds is not None and timeout expired.
            RuntimeError: If session wasn't created.
        """
        while self.__limit <= self.__amount:
            if timeout_seconds is not None:
                timeout_seconds -= sleep_seconds
                if timeout_seconds < 0:
                    raise TimeoutError
            await asyncio.sleep(sleep_seconds)

        # There is no guarantee that session will exist during
        #   operations of other tasks
        if self.__session is None:
            Logger.error("Cannot get session instance because ClientSession is not exists")
            raise RuntimeError("ClientSession is not exists")

        self.__amount += 1  # Acquire a slot
        Logger.debug("ClientSession slot is acquired (%s in total)", self.__amount)
        Logger.info("ClientSession is successfully shared")
        try:
            yield self.__session  # Make session available
        except Exception as exc:
            Logger.warning("Some exception occurred during sharing session: %s", exc)
            raise
        finally:
            # This block guarantees that amount will safely decrease
            self.__amount -= 1  # Free the slot
            Logger.debug("ClientSession slot was free (%s in total)", self.__amount)
            Logger.info("ClientSession sharing is ended")
