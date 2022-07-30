# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains `PartialRequestBuilder` class that allows to create template requests.

This class allows to create template requests with deferred and required fields.

Examples:
    >>> import time
    >>>
    >>>
    >>> request = (
    >>>     PartialRequestBuilder("GET")
    >>>     .with_url("youtube.com/watch?v={video}",
    >>>               PartialSection(automatic={},
    >>>                              filled={},
    >>>                              required={"video"}))
    >>>     .with_section("params",
    >>>                   PartialSection(automatic={
    >>>                                      "time": lambda: str(time.time())},
    >>>                                  filled={"from": "google.com"},
    >>>                                  required={"user"}))
    >>>     .build())
"""
import logging

from dataclasses import dataclass, field
from typing import TypeAlias

from .partial import PartialRequest
from .section import PartialSection

Logger = logging.getLogger(__file__)

# TODO: Alias to Self from Python 3.11
Self: TypeAlias = "PartialRequestBuilder"


@dataclass
class PartialRequestBuilder:
    """`PartialRequestBuilder` allows to create template requests.

    This class allows to create template requests with deferred and required
    fields. The first one allows to defer field evaluation (e.g. get current
    time at the request sending stage). The second one allows to throw
    a RuntimeError on attempting to send unready request.

    Example:
        Using unreadied request

        >>> from downloader.client import Client
        >>>
        >>>
        >>> request = (
        >>>     PartialRequestBuilder("GET")
        >>>     .with_url("youtube.com/watch?v={video}",
        >>>               PartialSection(automatic={},
        >>>                              filled={},
        >>>                              required={"video"}))
        >>>     .build())
        >>>
        >>> async with Client().create() as client:
        >>>     async with client.session() as session:
        >>>         async with request.make(session) as response:
        >>>             pass  # Unreachable: "video" field is not ready, RuntimeError

        Using readied request

        >>> from downloader.client import Client
        >>>
        >>>
        >>> request = (
        >>>     PartialRequestBuilder("GET")
        >>>     .with_url("youtube.com/watch?v={video}",
        >>>               PartialSection(automatic={},
        >>>                              filled={},
        >>>                              required={"video"}))
        >>>     .build())
        >>>
        >>> request = request.with_url_fields(parameters={"video": "jNQXAC9IVRw"})
        >>>
        >>> async with Client().create() as client:
        >>>     async with client.session() as session:
        >>>         async with request.make(session) as response:
        >>>             pass  # All is fine
    """
    __method: str
    __url: str | None = field(default=None)
    __url_section: PartialSection = field(default_factory=PartialSection)
    __sections: dict[str, PartialSection] = field(default_factory=dict)

    def build(self) -> PartialRequest:
        """Builds a new `PartialRequest` from builder instance.

        A new `PartialRequest` have same behavior as template, so it's fine
        reuse built partial request.

        Note: Auto fields are not evaluates.

        Examples:
            >>> request = (
            >>>     PartialRequestBuilder("GET")
            >>>     .with_url("youtube.com/watch?v={video}",
            >>>               PartialSection(automatic={},
            >>>                              filled={},
            >>>                              required={"video"}))
            >>>     .build())

        Returns:
            PartialRequest: A partial initialized request that will be
                ready on `PartialRequest.make`

        Raises:
            RuntimeError: When url is not set.
        """
        if self.__url is None:
            Logger.error("Url wasn't set for %s", self)
            raise RuntimeError(f"Url wasn't set for {self}")

        Logger.debug("Creating PartialRequest from %s", self)
        return PartialRequest(
            self.__method, self.__url, self.__url_section, self.__sections)

    def with_section(self, kind: str, section: PartialSection) -> Self:
        """Adds a new section (updates existed) with the specified kind.

        Creates or updates existing one section of http request.
        Section is just a part of http request (e.g. cookies, params, headers).
        Section updates via `PartialSection.update` method (see that method
        for more information).

        Examples:
            >>> import time
            >>>
            >>>
            >>> request = (
            >>>     PartialRequestBuilder("GET")
            >>>     .with_url("youtube.com")
            >>>     .with_section("params",
            >>>                   PartialSection(automatic={
            >>>                                      "time": lambda: str(time.time())},
            >>>                                  filled={"from": "google.com"},
            >>>                                  required={"user"}))
            >>>     .build())

        Args:
            kind: Name of section kind (e.g. headers)
            section: The content of a section to be added (updated).

        Returns:
            Self instance for chaining method call.
        """
        Logger.debug("Section %s was added")
        self.__sections[kind] = self.__sections.get(kind, PartialSection)
        self.__sections[kind].update(section)
        return self

    def with_url(self, url: str, section: PartialSection | None = None) -> Self:
        """Sets url and format fields via section.

        Sets url and all automatic, filled and requried fields into builder
        overriding previous url and its section. `PartialSection` is used
        because it allows to have deferred and required fields in url template.
        Url can be simple string, without any fields. In that case only url
        string must be provided.

        Examples:
            >>> request_with_url_fields = (
            >>>     PartialRequestBuilder("GET")
            >>>     .with_url("youtube.com/watch?v={video}",
            >>>               PartialSection(automatic={},
            >>>                              filled={},
            >>>                              required={"video"}))
            >>>     .build())
            >>>
            >>> simple_request = (
            >>>     PartialRequestBuilder("GET")
            >>>     .with_url("youtube.com")
            >>>     .build())

        Args:
            url: The url for resource. Can use format for auto fields.
            section: The fields to be unpacked in `url.format` later.

        Returns:
            Self instance for chaining method call.
        """
        Logger.debug("Url %s was added", url)
        self.__url = url
        self.__url_section = section or PartialSection()
        return self
