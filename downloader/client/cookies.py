# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains `CookiesStorage` class that allows to keep cookies.

`CookiesStorage` is a class for collecting and reusing cookies from client session.
Normally, you just need to provide the instance for collection cookies.

Warning:
    For coping or moving cookies you just need to copy or move entire folder
    (please, left cookies/README.md for more consistence of project).

Example:
    >>> from downloader.client import Client
    >>>
    >>>
    >>> storage = CookiesStorage()
    >>> # For custom directory you can provide it
    >>> # from pathlib import Path
    >>> # storage = CookiesStorage(Path().home() / "cookies")
    >>>
    >>> async with Client(storage=storage).create() as client:
    >>>     async with client.session() as session:
    >>>         async with session.get("example.com") as response:
    >>>             pass  # Do some stuff
"""
import asyncio
import json
import hashlib
import logging
import pickle

from http.cookies import SimpleCookie
from pathlib import Path

import aiofiles


Logger = logging.getLogger(__file__)


class CookiesStorage:
    """`CookiesStorage` represents `SimpleCookies` that store locally.

    `CookiesStorage` is the only one way to collect and reuse cookies from the sites.
    This class is not designed to be used manually, but it is also possible.
    For more information, see `CookiesStorage` method.

    Note: in case if you want to move or copy `CookiesStorage` do it manually
    by **COPING** or **MOVING** the `CookiesStorage` directory. Default location:
    downloader/client/cookies

    Examples:
        `CookiesStorage` allows to keep collected cookies from the sites
        and automaticly load it in the next application launch.

        >>> from downloader.client import Client
        >>>
        >>>
        >>> storage = CookiesStorage()
        >>>
        >>> async with Client(storage=storage).create() as client:
        >>>     async with client.session() as session:
        >>>         async with session.get("example.com") as response:
        >>>             pass  # Do some stuff

        Later cookies can be accessed via standard method. Note that,
        `Client` uses `CookiesStorage` automaticly, so it is enough to
        provide the storage.

        >>> from downloader.client import Client
        >>>
        >>>
        >>> storage = CookiesStorage()
        >>> await storage.load()
        >>>
        >>> assert "example.com" in storage.domains()  # PASSES
    """
    HOMEPATH = Path(__file__).parent / "cookies"

    def __init__(self, dirpath: Path | None = None) -> None:
        """Creates a new CookiesStorage instance.

        Args:
             dirpath: Path to a directory where cookies located. This path will use
                for loading and saving all cookies. If None provided, default path
                is using (see CookiesStorage.HOMEPATH).
        """
        self.__domains: dict[str, SimpleCookie] = {}
        self.__dirpath = dirpath or self.HOMEPATH
        self.__index = self.__dirpath / "domains.json"

    def domains(self) -> dict[str, SimpleCookie]:
        """Returns loaded domains as mapping of domains and SimpleCookies instances.

        This method must be used only as payload or default cookies for `Client`.
        By default, `Client` uses the instance of CookiesStorage independently,
        so no action needed.

        Returns:
             Copy of internal mapping with domains and SimpleCookie instances.
                Use `update` method for changing cookies.
        """
        Logger.debug("Domains copy was created")
        return self.__domains.copy()

    async def delete(self, *domains: str) -> None:
        """Deletes all domains from index file and local storage.

        Deletes all domains that exist on the local storage (whatever it locates).
        Firstly updates index file. Next tries to delete cookie file. When file
        is not exist on the local storage it passes.

        Examples:
            All storages must be saved at least once (it does automaticly when
            using `Client`)

            >>> storage = CookiesStorage()  # Storage with default HOMEPATH
            >>>
            >>> await storage.delete("example.com")  # Error if no domains.json in HOMEPATH

        Args:
             *domains: Domain string that must be deleted.

        Raises:
            FileNotFoundError: When index file is not exist.
            TypeError: When deserialized object from index file is not a `dict`.
        """
        if not self.__index.exists():
            Logger.error("Index file is not exist at %s", self.__index)
            raise FileNotFoundError(f"Index file is not exist at {self.__index}")

        async with aiofiles.open(self.__index, mode="r") as file:
            stored = json.loads(await file.read())

        if not isinstance(stored, dict):
            Logger.error("Loaded domains have wrong type %s", type(stored))
            raise TypeError(f"Domains must be a dict[str, str] not a {type(stored)}")
        Logger.debug("Domains were successfully loaded")

        # Collect files to remove, flush index
        removed = {stored[domain] for domain in domains if domain in stored}
        flushed = {domain: stored[domain] for domain in stored if domain not in domains}

        # Firstly save updated index file
        #   In case if some error occurs it better to have the correct index
        async with aiofiles.open(self.__index, mode="w") as file:
            await file.write(json.dumps(flushed, indent=4, sort_keys=True))
        Logger.debug("Flushed index file was successfully saved")

        for filename in removed:
            self.__dirpath.joinpath(filename).unlink(missing_ok=True)
            Logger.debug("Cookie file %s was unlinked", filename)

        Logger.info("Domains were successfully removed: %s", domains)

    async def load_domain(self, domain: str, filename: str) -> None:
        """Loads cookie file from filename and sets/updates domain cookie.

        Firstly cookie loads from the filename in `CookiesStorage` directory and
        checks is it SimpleCookie. If is it, then set a new domain or the existed
        one (by `dict.get`) and updates it (or a new empty `SimpleCookie`).

        Warning:
            This method must not be used, use `save`, `update` and `load` instead.

        Examples:
            >>> import hashlib
            >>> import pickle
            >>>
            >>> from http.cookies import SimpleCookie
            >>>
            >>>
            >>> storage = CookiesStorage()
            >>> await storage.load()
            >>>
            >>> with open("filename", mode="wb") as file:
            >>>     cookie = SimpleCookie({"user": "Helltraitor"})
            >>>     file.write(pickle.dumps(cookie, protocol=5))
            >>>
            >>> domain = "example.com"
            >>> filename = hashlib.md5(domain.encode("utf-8")).hexdigest()
            >>>
            >>> await storage.load_domain(domain, filename)  # Now storage have a new cookie

        Args:
            domain: Domain string that will be used as the key of index `dict`.
            filename: Filename that will be loaded from `CookiesStorage` directory.

        Raises:
            TypeError: When deserialized object from cookie file is not a `SimpleCookie`.
        """
        async with aiofiles.open(self.__dirpath / filename, mode="rb") as file:
            Logger.debug("Loading pickled cookie of %s", domain)
            cookie = pickle.loads(await file.read())

        if not isinstance(cookie, SimpleCookie):
            Logger.error("Cookie of %s must be SimpleCookie not %s", domain, type(cookie))
            raise TypeError(f"Cookie of {domain} must be SimpleCookie not {type(cookie)}")

        self.__domains[domain] = self.__domains.get(domain, SimpleCookie())
        self.__domains[domain].update(cookie)
        Logger.info("Cookie at %s was successfully loaded", domain)

    async def load(self) -> None:
        """Loads index file and its domains cookies from local storage.

        Firstly loads index file, then loads all domains cookies concurrently.
        When index file is not exist does nothing (because it is fine to not
        have nay files at the first launch).

        Examples:
            >>> from downloader.client import Client
            >>>
            >>>
            >>> storage = CookiesStorage()
            >>> await storage.load()

        Raises:
            TypeError: When deserialized object from index file is not a `dict`.
            TypeError: When deserialized object from cookie file is not a `SimpleCookie`.
        """
        if not self.__index.exists():
            Logger.info("Index file is not exist at %s", self.__index)
            return

        async with aiofiles.open(self.__index, mode="r") as file:
            domains = json.loads(await file.read())

        if not isinstance(domains, dict):
            Logger.error("Loaded domains have wrong type %s", type(domains))
            raise TypeError(f"Domains must be a dict[str, str] not a {type(domains)}")

        Logger.info("Domains index file was successfully loaded at %s", self.__index)
        await asyncio.gather(*(self.load_domain(*domain) for domain in domains.items()))

    async def save_domain(self, domain: str, filename: str) -> None:
        """Saves `SimpleCookie` from domain in filename.

        Creates or rewrites the cookie filename and save `SimpleCookie`
        as pickled object with fifth protocol.

        Warning:
            This method must not be used, use `update` instead.

        Examples:
            >>> import hashlib
            >>> import pickle
            >>>
            >>> from http.cookies import SimpleCookie
            >>>
            >>>
            >>> storage = CookiesStorage()
            >>> await storage.load()
            >>>
            >>> with open("filename", mode="wb") as file:
            >>>     cookie = SimpleCookie({"user": "Helltraitor"})
            >>>     file.write(pickle.dumps(cookie, protocol=5))
            >>>
            >>> domain = "example.com"
            >>> filename = hashlib.md5(domain.encode("utf-8")).hexdigest()
            >>>
            >>> # Cookie contains in the folder but NOT in the storage
            >>> await storage.save_domain(domain, filename)

        Args:
            domain: Used as the key of index `dict` for saving domain `SimpleCookie`.
            filename: Filename that will save domain `SimpleCookie` in `CookiesStorage`
                directory.

        Raises:
            KeyError: When domain is not exists in index `dict`.
        """
        Logger.debug("Saving domain %s", domain)
        async with aiofiles.open(self.__dirpath / filename, mode="wb") as file:
            await file.write(pickle.dumps(self.__domains[domain], protocol=5))
        Logger.info("Domain %s was successfully saved", domain)

    async def save(self):
        """Saves `CookiesStorage` into its directory.

        Firstly loads an actual file index, checks its type and updates index `dict`.
        Then saves all domains cookies concurrently. After all, saves file index.
        This is kind of safeguard for case when file index will not save. In that
        case entire application will be broken, instead of partial braking and
        undefined behavior.

        Warning:
            Normally you do not need to use `save` method, use `update` instead
            (saves automatically).

        Raises:
             TypeError: When deserialized object from index file is not a `dict`.
        """
        # Actualizing file index
        Logger.debug("Loading actual index file")
        async with aiofiles.open(self.__index, mode="w+") as file:
            domains = json.loads(await file.read() or "{}")

        if not isinstance(domains, dict):
            Logger.error("Loaded domains have wrong type %s", type(domains))
            raise TypeError(f"Domains must be a dict[str, str] not a {type(domains)}")
        Logger.info("Actual index file was successfully loaded")

        # Saving `SimpleCookie` by hex domain name
        updated = {key: hashlib.md5(key.encode("utf-8")).hexdigest()
                   for key in self.__domains}
        Logger.debug("Save domains with some updates: %s", list(updated))

        Logger.debug("Saving new `SimpleCookie` files")
        await asyncio.gather(*(self.save_domain(*domain) for domain in updated.items()))

        # Saving index file
        Logger.debug("Saving index file at %s", self.__index)
        async with aiofiles.open(self.__index, mode="w+") as file:
            domains = json.loads(await file.read() or "{}") | updated
            await file.seek(0)
            await file.write(json.dumps(domains, indent=4, sort_keys=True))
        Logger.info("`CookiesStorage` was successfully saved")

    async def update(self, domains: dict[str, SimpleCookie]) -> None:
        """Updates/creates cookies and save `CookiesStorage`.

        Updates or creates a new cookies one by one, then saves entire `SimpleCookie`.
        For more information see `save` method.

        Examples:
            >>> from http.cookies import SimpleCookie
            >>>
            >>>
            >>> cookie = SimpleCookie({"user": "Helltraitor"})
            >>>
            >>> storage = CookiesStorage()
            >>> await storage.load()
            >>> await storage.update({"example.com": cookie})  # Saves automatically

        Args:
            domains: Mapping of domain names and its `SimpleCookies` objects.
        """
        for domain, cookie in domains.items():
            self.__domains[domain] = self.__domains.get(domain, SimpleCookie())
            self.__domains[domain].update(cookie)
        await self.save()
