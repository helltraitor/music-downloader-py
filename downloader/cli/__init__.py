# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This package represents cli implementation via `click` package.

This package is not designed for using by other applications, packages,
libraries, modules or scripts. But it is possible (see examples).

This package contains `main` function that is the entry application point.
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
from .main import main

# Initialization imports
#   Import in python executes code in the modules. Without these imports,
#   `click` package will never know about set commands, arguments and options
#   from these modules.
from .cookies import cookies as _cookies
from .fetcher import fetch as _fetch
