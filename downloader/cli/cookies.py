# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains cookie part of cli.

This module contains `cookies` function that is used by `click` package.
Other functions are helpers that performs the specified action.
"""
import asyncio
import logging

from http.cookies import SimpleCookie
from pathlib import Path

import click

from downloader.client import CookiesStorage

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
    if not isinstance(context.obj, dict):
        Logger.error("Context.obj must have dict type, not a %s", type(context.obj))
        raise TypeError(f"Context.obj must have dict type, not a {type(context.obj)}")

    dirpath = context.obj.get("cookies", None)
    if dirpath is not None and not isinstance(dirpath, Path):
        Logger.error("Cookies in context must have Path type, not a %s", type(dirpath))
        raise TypeError(f"Cookies in context must have Path type, not a {type(dirpath)}")

    storage = CookiesStorage(dirpath)
    match action:
        case "DELETE":
            if key is not None:
                # SAFE: Key cannot be set without domain
                asyncio.run(cookies_delete_exact(storage, domain, key))  # type: ignore
            elif domain is not None:
                if force or click.confirm("Delete the domain?"):
                    asyncio.run(cookies_delete_domain(storage, domain))
            else:
                if force or click.confirm("Delete all domains?"):
                    asyncio.run(cookies_delete_all(storage))

        case "GET":
            if key is not None:
                # SAFE: Key cannot be set without domain
                asyncio.run(cookies_get_exact(storage, domain, key))  # type: ignore
            elif domain is not None:
                asyncio.run(cookies_get_domain(storage, domain))
            else:
                asyncio.run(cookies_get_all(storage))

        case "SET":
            if value is not None:
                # SAFE: Value cannot be set without both key and domain
                asyncio.run(cookies_set(storage, domain, key, value))  # type: ignore
            else:
                Logger.error("Unable to set cookie without both domain, key and value")
                raise ValueError("Unable to set cookie without both domain, key and value")

        case _:
            Logger.error("Command is not recognized %s", action)
            raise ValueError(f"Cookie command {action} is not recognized")


async def cookies_delete_all(storage: CookiesStorage) -> None:
    """Deletes all domains from cookie storage.

    This function can be used only as an example of preformed action.

    Args:
        storage: CookiesStorage instance.
    """
    await storage.load()
    await storage.delete(*storage.domains())


async def cookies_delete_domain(storage: CookiesStorage, domain: str) -> None:
    """Deletes whole domain from cookie storage.

    This function can be used only as an example of preformed action.

    Args:
        storage: CookiesStorage instance.
        domain: Domain string (e.g. example.com).
    """
    await storage.load()
    await storage.delete(domain)


async def cookies_delete_exact(storage: CookiesStorage, domain: str, key: str) -> None:
    """Deletes exact pair of the key and a value from storage.

    This function can be used only as an example of preformed action.

    Args:
        storage: CookiesStorage instance.
        domain: Domain string (e.g. example.com).
        key: Key string from specified domain.
    """
    await storage.load()
    if cookie := storage.domains().get(domain, None):
        cookie.pop(key, None)
        await storage.update({domain: cookie})


async def cookies_get_all(storage: CookiesStorage) -> None:
    """Prints all domains and their cookie's keys and values into stdout.

    This function can be used only as an example of preformed action.

    Args:
        storage: CookiesStorage instance.
    """
    await storage.load()
    for domain, cookie in storage.domains().items():
        click.echo(f"Domain {domain}")
        for key, morsel in cookie.items():
            click.echo(f"\t{key}\t{morsel.value}")


async def cookies_get_domain(storage: CookiesStorage, domain: str) -> None:
    """Prints all cookie's keys and values from the domain into stdout.

    This function can be used only as an example of preformed action.

    Args:
        storage: CookiesStorage instance.
        domain: Domain string (e.g. example.com).
    """
    await storage.load()
    cookie = storage.domains().get(domain, SimpleCookie())
    for key, morsel in cookie.items():
        click.echo(f"\t{key}\t{morsel.value}")


async def cookies_get_exact(storage: CookiesStorage, domain: str, key: str) -> None:
    """Prints the value of the key from the domain into stdout.

    This function can be used only as an example of preformed action.

    Args:
        storage: CookiesStorage instance.
        domain: Domain string (e.g. example.com).
        key: Key string from specified domain.
    """
    await storage.load()
    cookie = storage.domains().get(domain, SimpleCookie())
    if morsel := cookie.get(key, None):
        click.echo(morsel.value)


async def cookies_set(storage: CookiesStorage, domain: str, key: str, value: str) -> None:
    """Sets the specified value in the domain with a key.

        This function can be used only as an example of preformed action.

        Args:
            storage: CookiesStorage instance.
            domain: Domain string (e.g. example.com).
            key: Key string from specified domain.
    """
    await storage.load()
    cookie = storage.domains().get(domain, SimpleCookie())
    cookie[key] = value
    await storage.update({domain: cookie})
