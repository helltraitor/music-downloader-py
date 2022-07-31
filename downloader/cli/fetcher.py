# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains fetch part of cli.

This module contains `fetcher` function that is used by `click` package.
Other functions are helpers that performs the specified action.
"""
import asyncio
import logging
import typing

from pathlib import Path

import click

from downloader import domains
from downloader.client import Client, CookiesStorage, RateLimit
from downloader.domains import Fetchable
from downloader.fetcher import Fetcher, Target
from downloader.filesystem import FileSystem, FileSystemConflict

from .main import main


Logger = logging.getLogger(__file__)


@main.command()
@click.option("-c", "--conflict",
              default="ERROR",
              help="""Action in the case when the destination folder contains
                      the same file as downloaded one. Default is ERROR,
                      in that case the application will interrupt and shutdown.
                      IGNORE makes the application to ignore the issues and
                      continue work. OVERRIDE makes the application to override
                      all conflicting files.""",
              type=click.Choice(["ERROR", "IGNORE", "OVERRIDE"], case_sensitive=False),
              show_default=True)
@click.option("-d", "--dest",
              help="""Destination folder. Path supports expanding so it's
                      fine to use `~/` or `%USERPROFILE%`""",
              type=click.Path(file_okay=False, resolve_path=True, path_type=Path),
              required=True)
@click.option("-l", "--limit",
              default=4,
              help="Limit of the number of tracks that can be downloaded at one time",
              type=click.IntRange(1, 8),
              show_default=True)
@click.option("-o", "--options",
              help="Options that will be applied for domain that matches url host.",
              multiple=True)
@click.argument("targets", nargs=-1)
@click.pass_context
def fetch(context: click.Context,  # pylint: disable=locally-disabled, too-many-arguments, too-many-locals
          targets: tuple[str],
          conflict: str,
          dest: Path,
          limit: int,
          options: tuple[str]) -> None:
    """Fetches musics from all url targets applying tags and cover.

    \b
    Urls will be processed by host models so result may vary. For now
    the following sources are supported:
        Yandex Music (domain yandex.ru, key Session_id)

    \b
    Examples:
        | downloader fetch <url1> <url2> ... <urlN> -d %USERPROFILE%/Downloads
        | downloader fetch <url> -d %USERPROFILE%/Downloads
        | downloader fetch <url> -d %USERPROFILE%/Downloads -c ignore
        | downloader fetch <url> -d %USERPROFILE%/Downloads -c ignore -l 8
        | downloader fetch <url> -d %USERPROFILE%/Downloads -o HighQuality -o RussianLyrics

    \f
    Note (for documentation in `click` package):
        \b - disables wrapping for docs
        \f - truncate docs.

    Args:
        context: `Click` package context that may contain extra information.
        targets: The list of url strings. Each one must be determined
            by host and process by host models.
        conflict: Action to preform when file with the same name already
            exists. The one of the following variants `ERROR`, `IGNORE`,
            `OVERRIDE` (`ERROR` is default).
        dest: The destination folder for fetching music. Guarantees to be
            valid by `click` package.
        limit: The download limit. Guarantees to be in [1, 8]
            (by `click` package).
        options: Any options tuple that must be supported by domains. These
            options will be used for setup domain. See about `domain name`
            for more information.
    """
    variants = {variant.name: variant for variant in FileSystemConflict}
    if conflict not in variants:
        Logger.error("Conflict value %s not in %s",
                     conflict, list(variants.keys()))
        raise ValueError(f"Conflict name {conflict} is not acceptable")

    if limit not in typing.get_args(RateLimit):
        Logger.error("Limit value %s is out of bounds %s",
                     limit, list(typing.get_args(RateLimit)))
        raise ValueError(f"Limit {limit} is out of bounds")

    separated = {}
    for name, subclass in domains.ALL.items():
        acceptable = {target for target in targets if subclass.match(target)}
        if not acceptable:
            continue

        if not issubclass(subclass, Fetchable):
            Logger.error("%s is not support fetching", name)
            raise RuntimeError(f"{name} cannot be used for fetching")
        separated[subclass] = acceptable

    activated = []
    for subclass, subtargets in separated.items():
        factory = subclass()
        # SAFE: Subclass implements both Domain and Fetchable
        factory.activate(list(options))  # type: ignore
        activated.extend([factory.fetch_from(target) for target in subtargets])

    # SAFE: Cookies ensures to be in main cli `click` function.
    #   `cookies` can be Path or None (last is safe for passing)
    storage = CookiesStorage(dirpath=context.obj["cookies"])
    # SAFE: Limit was checked above
    client = Client(limit=limit, storage=storage)  # type: ignore

    system = FileSystem(variants[conflict], dest)
    asyncio.run(fetch_all(activated, client, system))


async def fetch_all(targets: list[Target], client: Client, system: FileSystem) -> None:
    """Fetches all targets according to `Fetcher.fetch_all` method.

    For more information see `Fetcher.fetch_all` and `Fetcher.fetch` methods.

    Args:
        targets: List of `Target` objects (`Downloadable` or `Expandable`)
        client: The raw client instance that will be used for creating a ClientSession.
        system: The file system with a root in the specified directory.
    """
    async with client.create() as client:
        await Fetcher(client).fetch_all(targets, system)
