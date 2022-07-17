# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This is the entry point of downloader application.

In this module nothing interesting, at all. Literally just cli import
and argument processing in `if __name__ == '__main__'` block.
"""
from downloader import cli


if __name__ == '__main__':
    # cli.main is decorated so this is fine to use it like this (see docs)
    cli.main()  # pylint: disable=locally-disabled, no-value-for-parameter
