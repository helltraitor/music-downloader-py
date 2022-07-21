# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains cookie part of cli.

This module contains `cookies` function that is used by `click` package.
Other functions are helpers that performs the specified action.
"""
import logging

import click

from .main import main


Logger = logging.getLogger(__file__)


@main.command()
@click.option("-f", "--force",
              default=False,
              is_flag=True,
              show_default=True,
              help="""Disables confirmation dialog when
                      delete all domains or whole domain.""")
@click.argument("action",
                type=click.Choice(["DELETE", "GET", "SET"], case_sensitive=False))
@click.argument("domain", default=None, required=False)
@click.argument("key", default=None, required=False)
@click.argument("value", default=None, required=False)
@click.pass_context
def cookies(context: click.Context, action: str,  # pylint: disable=locally-disabled, too-many-arguments
            domain: str | None, key: str | None, value: str | None,
            force: bool) -> None:
    """Preforms an indicated action on the cookie with domain, key and value.

    \b
    Accepts one positional argument from the following variants:
        DELETE have no requirements. Optional is a domain or both the domain
            and a key. When no domain provided, deletes all domains. When
            a domain provided, deletes whole domain. And when both the domain
            and a key are provided, deletes a pair of the key and its value
            from the specified domain.
        GET have no requirements. Optional is a domain or both the domain and
            a key. When no domain provided, displays all domains. When
            a domain provided, displays all keys in the domain. And when both
            the domain and a key provided, displays key's value.
        SET requires both domain, key and value. Set has the updating behavior.
            That means that you can safely set keys and values one by one
            in the specified domain. In the case when key already exists,
            its value override by the given value.

    \b
    Examples:
        | downloader cookies delete example.com
        | downloader cookies delete example.com SomeKey
        | downloader cookies get example.com
        | downloader cookies get example.com SomeKey
        | downloader cookies set example.com SomeKey SomeValue

    \f
    Note (for documentation in `click` package):
        \b - disables wrapping for docs
        \f - truncate docs.

    Args:
        context: `Click` package context that may contain cookies directory.
        action: Action parameter from variants `DELETE`, `GET` or `SET`.
        domain: Optional domain string (e.g. yandex.ru)
        key: Optional cookie key (optional for delete).
        value: Optional cookie value (used only by set).
        force: Disables confirmation dialog when delete all domains or whole domain.
    """
