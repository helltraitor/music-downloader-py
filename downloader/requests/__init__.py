# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This package contains partial request class, builder and section.

`PartialRequest` allows to defer field evaluation and to require some fields
to be set before request making (including url section). Url also can be section.
That allows to use deferred and required fiedls in url template (must support
`str.format` method).

Warning:
    The `PartialRequest` can be created with a default constructor, but
    it is highly recommended to create an instance via `PartialRequestBuilder`.

Examples:
    >>> import time
    >>>
    >>> from downloader.client import Client
    >>> from downloader.requests import (
    >>>     PartialRequest, PartialRequestBuilder, PartialSection
    >>> )
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
    >>>
    >>> request = (
    >>>     request
    >>>     .with_url_fields(parameters={"video": "jNQXAC9IVRw"})
    >>>     .with_section_fields("params", parameters={"user": "Helltraitor"}))
    >>>
    >>> async with Client().create() as client:
    >>>     async with client.session() as session:
    >>>         async with request.make(session) as response:
    >>>             pass  # All is fine
"""
from .builder import PartialRequestBuilder
from .partial import PartialRequest
from .section import PartialSection
