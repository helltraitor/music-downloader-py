# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains `PartialRequest` class that allows to use requests as templates.

This request class allows to use deferred evaluated fields (automatic),
and makes sure that all required fields are satisfied at making request
stage.

Warning:
    The instance can be created with a default constructor, but it is highly
    recommended to create an instance via `PartialRequestBuilder`.

Examples:
    >>> from downloader.client import Client
    >>> from downloader.requests import PartialRequestBuilder
    >>>
    >>>
    >>> request = (
    >>>     PartialRequestBuilder("GET")
    >>>     .with_url("youtube.com")
    >>>     .build())
    >>>
    >>> # Same as above
    >>> _alt_request = PartialRequest("GET",
    >>>                               "youtube.com",
    >>>                               PartialSection(),
    >>>                               {})
    >>>
    >>> async with Client().create() as client:
    >>>     async with client.session() as session:
    >>>         async with request.make(session) as response:
    >>>             pass  # All is fine
"""
import contextlib
import copy
import logging

from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any, TypeAlias

from aiohttp import ClientSession, ClientResponse

from .section import PartialSection


Logger = logging.getLogger(__file__)

# TODO: Alias to Self from Python 3.11
Self: TypeAlias = "PartialRequest"


@dataclass
class PartialRequest:
    """`PartialRequest` is a template request.

    This request class allows to use deferred evaluated fields (automatic),
    and makes sure that all required fields are satisfied at making request
    stage.

    Warning:
        The instance can be created with a default constructor, but it is highly
        recommended to create an instance via `PartialRequestBuilder`.

    Examples:
            >>> from downloader.client import Client
            >>> from downloader.requests import PartialRequestBuilder
            >>>
            >>>
            >>> request = (
            >>>     PartialRequestBuilder("GET")
            >>>     .with_url("youtube.com")
            >>>     .build())
            >>>
            >>> # Same as above
            >>> _alt_request = PartialRequest("GET",
            >>>                               "youtube.com",
            >>>                               PartialSection(),
            >>>                               {})
            >>>
            >>> async with Client().create() as client:
            >>>     async with client.session() as session:
            >>>         async with request.make(session) as response:
            >>>             pass  # All is fine
    """
    __method: str
    __url: str
    __url_section: PartialSection
    __sections: dict[str, PartialSection]

    def ready(self) -> bool:
        """Checks if the request is ready to be made.

        Checks url section and all other section by `PartialSection.ready` method.

        Returns:
            Boolean that indicates ready state.
        """
        sections = all(section.ready() for section in self.__sections.values())
        return sections and self.__url_section.ready()

    @contextlib.asynccontextmanager
    async def make(self, session: ClientSession) -> AsyncIterator[ClientResponse]:
        """Makes a request via the ClientSession and returns a ClientResponse in the context.

        On this stage, request sections are unwraped into evaluted values
        and url template become formatted url (via the url section and
        `str.format`). In case, when some section (include the url section)
        is not ready, raises a RuntimeError.

        Examples:
            >>> from downloader.client import Client
            >>> from downloader.requests import PartialRequestBuilder
            >>>
            >>>
            >>> request = (
            >>>     PartialRequestBuilder("GET")
            >>>     .with_url("youtube.com")
            >>>     .build())
            >>>
            >>> async with Client().create() as client:
            >>>     async with client.session() as session:
            >>>         async with request.make(session) as response:
            >>>             pass  # All is fine

        Args:
            session: ClientSession instance.

        Returns:
            ClientResponse instance as context value.

        Raises:
            RuntimeError: When request is not ready.
        """
        if not self.ready():
            Logger.error("PartialRequest is not ready: %s", self)
            raise RuntimeError(f"PartialRequest is not ready: {self}")

        sections = {kind: section.unwrap() for kind, section in self.__sections.items()}
        url = self.__url.format(**self.__url_section.unwrap())

        async with session.request(self.__method, url, **sections) as response:
            Logger.info("Request was successfully make for %s", self)
            yield response

    def with_section_fields(
            self,
            kind: str,
            *,
            parameters: dict[str, str] | None = None,
            automatic: dict[str, Callable[[], str]] | None = None) -> Self:
        """Copies the `PartialRequest` with specified fields and their values in specified kind.

        When an existed kind section added, sets all fields and remove
        satisfied requirements from this section kind. Otherwise, just
        adds a new section with specified automatic and filled parameters.

        Examples:
            >>> from downloader.client import Client
            >>> from downloader.requests import PartialRequestBuilder
            >>>
            >>>
            >>> request = (
            >>>     PartialRequestBuilder("GET")
            >>>     .with_url("example.com")
            >>>     .with_section("params",
            >>>                   PartialSection(automatic={},
            >>>                                  filled={},
            >>>                                  required={"user"}))
            >>>     .build())
            >>>
            >>> request = request.with_section_fields("params", parameters={"user": "Helltraitor"})
            >>>
            >>> async with Client().create() as client:
            >>>     async with client.session() as session:
            >>>         async with request.make(session) as response:
            >>>             pass  # All is fine

        Args:
            kind: Section name that will be updated (or set).
            parameters: Optional dict that will be used for updating (setting).
            automatic: Optional dict with deferred evaluated values that will
                be used for updating (setting).

        Returns:
            PartialRequest copy (copy makes for reusing of original request).
        """
        sections = copy.deepcopy(self.__sections)
        sections[kind] = sections.get(kind, PartialSection())
        sections[kind].update(PartialSection(automatic=(automatic or {}),
                                             filled=(parameters or {}),
                                             required=set()))
        return PartialRequest(self.__method,
                              self.__url,
                              copy.deepcopy(self.__url_section),
                              sections)

    def with_url_fields(self,
                        *,
                        parameters: dict[str, Any] | None = None,
                        automatic: dict[str, Callable[[], Any]] | None = None) -> Self:
        """Copies the `PartialRequest` with specified fields and their values in url section.

        The url section allows to use the url as a template (which must support
        `str.format` method). Any existed field in section overrides, some satisfied
        required fields are removed.

        Examples:
            >>> from downloader.client import Client
            >>> from downloader.requests import PartialRequestBuilder
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

        Args:
            parameters: Optional dict that will be used for updating (setting).
            automatic: Optional dict with defer evaluating values that will be
                used for updating (setting).

        Returns:
            PartialRequest copy (copy makes for reusing of original request).
        """
        url_section = copy.deepcopy(self.__url_section)
        url_section.update(PartialSection(automatic=(automatic or {}),
                                          filled=(parameters or {}),
                                          required=set()))
        return PartialRequest(self.__method,
                              self.__url,
                              url_section,
                              copy.deepcopy(self.__sections))
