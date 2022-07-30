# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This package contains `Domain` abstract class implementation.

These packages must not be used directly. Any subclass of `Domain` will be
registered automatically. The registered domains can be found in `domain.py`
file in `ALL` global variable.
"""
import importlib
import logging
import pathlib
import sys


Logger = logging.getLogger(__file__)

DOMAINS = pathlib.Path(__file__).parent

sys.path.append(str(DOMAINS))

for entity in DOMAINS.iterdir():
    if entity.name == "__init__.py":
        continue

    # All domains must implement `Domain` class that will register any subclass
    #   automatically. So these modules (packages) just need to be imported.
    importlib.import_module(entity.name)
    Logger.info("Package %s was successfully imported", entity.name)

sys.path.remove(str(DOMAINS))
