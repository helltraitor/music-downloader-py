# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains about part of cli.

This module contains `about` function that is used by `click` package.
Other functions are helpers that performs the specified action.
"""
import click

from downloader import domains
from .main import main


@main.command()
@click.argument("domain", default="")
def about(domain: str) -> None:
    """Provides information about specified domain or entire package.

    \b
    Displays information from __init__.py file of supported module,
    or displays the standard message. This allows user to understand
    which domains are supported.
    Also is possible to display information about package/application
    by ignoring domain argument (see example).

    \b
    Examples:
        | downloader about
        | downloader about yandex
        | downloader about youtube
        | downloader about example

    \b
    Latest (or any other unknown domains) must display:
        `example.com domain is not supported.`

     \f
    Note (for documentation in `click` package):
        \b - disables wrapping for docs
        \f - truncate docs.

    Args:
        domain: The domain string value (e.g. yandex.ru)
    """
    if not domain:
        click.echo(ABOUT)
        return

    implementation = domains.ALL.get(domain.lower())
    if implementation is None:
        click.echo(f"Domain {domain} is not found.")
    else:
        click.echo(implementation.__doc__)


ABOUT = """Music downloader application v1.0.0

This application allows to download any music from any domain.
List of implemented domain can be found in extensions folder
(one folder for one extension).

Supported domains:
    Yandex (Track, Album, Artist, Playlist, Label)

For now, only yandex domain supported (because its the only
one domain that author is used).
"""
