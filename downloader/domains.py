# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains `Domain` abstract class and protocols.

The `Domain` class represents any domain that can be used by this application.
Also, `Fetchable` protocol is defined here. This protocol allows to fetch items
from this domain.

Examples:
    >>> from downloader.domains import Domain, Fetchable
    >>> from downloader.fetcher import Downloadable
    >>>
    >>>
    >>> class SomeTarget(Downloadable):
    >>>     # Implementation omitted
    >>>     pass
    >>>
    >>>
    >>> # example.com
    >>> class Example(Domain, Fetchable):
    >>>     def fetch_from(self, url: str) -> Target:
    >>>         return SomeTarget()
    >>>
    >>>     @staticmethod
    >>>     def match(url: str) -> bool:
    >>>         return "example.com" in url
"""
import logging

from abc import abstractmethod, ABC
from typing import Protocol, runtime_checkable, Type, TypeAlias

from downloader.fetcher import Target


Self: TypeAlias = "Domain"

ALL: dict[str, Type[Self]] = {}

Logger = logging.getLogger(__file__)


class Domain(ABC):
    """The `Domain` abstract class represents any Domain that can be used by application.

    Before using, any domain must be checked for url support by `match` method.
    Then, appropriate classes will be activated with options if the last ones
    provided, otherwise these classes will be just used, according to the user
    requirements and implemented protocols. When the appropriate domain
    not implements necessary protocol, execution interrupts.

    Examples:
        >>> from downloader.domains import Domain, Fetchable
        >>> from downloader.fetcher import Downloadable
        >>>
        >>>
        >>> class SomeTarget(Downloadable):
        >>>     # Implementation omitted
        >>>     pass
        >>>
        >>>
        >>> # example.com
        >>> class Example(Domain, Fetchable):
        >>>     def fetch_from(self, url: str) -> Target:
        >>>         return SomeTarget()
        >>>
        >>>     @staticmethod
        >>>     def match(url: str) -> bool:
        >>>         return "example.com" in url
    """
    def __init_subclass__(cls, **kwargs) -> None:
        cls_name = cls.__name__
        if cls_name in ALL:
            Logger.error("Domain %s already registered", cls_name)
            raise RuntimeError(f"Domain {cls_name} already registered")
        Logger.info("Domain %s was successfully registered", cls_name)
        ALL[cls_name.lower()] = cls

    def activate(self, options: list[str]) -> None:
        """Setups the domain instance and activate supported options.

        Activates special features that supports by the domain (e.g. high quality).
        All options are strings that provided by user so this is fine to make them
        lower before checks.

        Args:
            options: Options list provided by user.
        """
        Logger.error("Domain %s is not support options %s", type(self).__name__, options)
        raise ValueError(f"Domain {type(self).__name__} is not support options {options}")

    @staticmethod
    @abstractmethod
    def match(url: str) -> bool:
        """Checks if url string belongs to the domain.

        Args:
             url: The full url string of suspected domain.

        Returns:
            The boolean value that represents affiliation of url.
        """


@runtime_checkable
class Fetchable(Protocol):  # pylint: disable=locally-disabled, too-few-public-methods
    """`Fetchable` protocol represents the domain that supports fetching from url.

    All domains that can fetch music from url must implement this protocol
    and be `Domain` subclass.

    Example:
        >>> from downloader.domains import Domain, Fetchable
        >>> from downloader.fetcher import Downloadable
        >>>
        >>>
        >>> class SomeTarget(Downloadable):
        >>>     # Implementation omitted
        >>>     pass
        >>>
        >>>
        >>> # example.com
        >>> class Example(Domain, Fetchable):
        >>>     def fetch_from(self, url: str) -> Target:
        >>>         return SomeTarget()
        >>>
        >>>     @staticmethod
        >>>     def match(url: str) -> bool:
        >>>         return "example.com" in url
    """
    def fetch_from(self, url: str) -> Target:
        """Creates a `Target` instance from url.

        Creates a target from the url string, that will be used by `Fetcher`.

        Args:
            url: The string url that will be used as parse source for `Target`

        Returns:
            `Target` instance (`Downloadable` or `Expandable`) that represents some item.
        """
