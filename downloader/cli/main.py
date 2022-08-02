# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module represents entry point of cli implementation via `click` package.

This module is not designed for using by other applications, packages,
libraries, modules or scripts. But it is possible (see examples).

This module contains `main` function that is the entry application point.
Other functions must not be used.

Examples:
    Example of typical using

    >>> from downloader import cli
    >>>
    >>>
    >>> if __name__ == "__main__":
    >>>     cli.main()

    Example of debugging

    >>> from click.testing import CliRunner
    >>>
    >>> from downloader import cli
    >>>
    >>>
    >>> if __name__ == "__main__":
    >>>     runner = CliRunner()
    >>>     runner.invoke(cli.main, "cookies delete --domain example.com".split())
"""
import datetime
import logging

from pathlib import Path

import click


@click.group()
@click.option("--cookies",
              default=None,
              type=click.Path(file_okay=False, resolve_path=True, path_type=Path),
              help="""Path to the cookies folder. By default it is using
                      downloader/client/cookies""")
@click.option("--debug",
              default=False,
              is_flag=True,
              show_default=True,
              help="""Runs the application in the debug mode.
                      Doesn't change the application behavior""")
@click.pass_context
def main(context: click.Context, cookies: Path | None, debug: bool) -> None:
    """Music downloader allows to fetch, update and track music content.

    \b
    Examples:
        | downloader cookies set --domain yandex.ru --key Session_id --value <CookieValue>
        | downloader fetch <url> -c ignore -d %USERPROFILE%/Downloads

    \f
    Note (for documentation in `click` package):
        \b - disables wrapping for docs
        \f - truncate docs.

    Args:
        context: `Click` package context that will be shared within other commands.
        cookies: Expanded path of cookies directory (or None for default).
        debug: Boolean variable that influence on logs. Logs are located in:
            `music-downloader-py/downloader/logs`
    """
    # Click context setup
    context.ensure_object(dict)
    context.obj["cookies"] = cookies

    # Logging setup
    log_filename = datetime.datetime.now().strftime("%Y-%m-%d %H_%M_%S.%f.log")
    log_filepath = Path(__file__).parent.parent / "logs" / log_filename

    logging.basicConfig(
        filename=log_filepath,
        format="%(asctime)s %(levelname)7s: %(filename)s %(funcName)s: %(message)s",
        level=logging.DEBUG if debug else logging.INFO)
