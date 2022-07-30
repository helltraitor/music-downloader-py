# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
"""This module contains `PartialSection` class that allows to easy manage http sections.

This class is necessary for requests with deferred fields and requests
with required params.

Examples:
    >>> import time
    >>>
    >>>
    >>> section = PartialSection(automatic={"time": lambda: str(time.time())},
    >>>                          filled={},
    >>>                          required={"user"})
    >>> # parameters = section.unwrap()  # Throws an error
    >>> section.update(PartialSection(automatic={"user": lambda: "Helltraitor"},
    >>>                                  filled={},
    >>>                                  required=set()))
    >>> parameters = section.unwrap()  # All is fine
"""
import logging

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeAlias

Logger = logging.getLogger(__file__)

# TODO: Alias to Self from Python 3.11
Self: TypeAlias = "PartialSection"


@dataclass
class PartialSection:
    """`PartialSection` is a dataclass for http section fields.

    The main features are deferring field evaluation and requirements
    for the fields at the unwrapping stage.

    This class was created for more simple tracking of requirement fields.
    For example, an instance of this class will throw a `RuntimeError`,
    when programmer forget to add some required fields for api.

    Warning:
        It is important to separate cookies from raw requests. The first are set
        on making request stage but other sections (such like params) are set
        on building request stage.
    """
    automatic: dict[str, Callable[[], str]] = field(kw_only=True, default_factory=dict)
    filled: dict[str, str] = field(kw_only=True, default_factory=dict)
    required: set[str] = field(kw_only=True, default_factory=set)

    def ready(self) -> bool:
        """Checks if `PartialSection` ready to unwrap

        `PartialSection` is ready when all required fields are set. It's possible
        to do via update method (see `update` for more information).

        Examples:
            >>> section = PartialSection(automatic={}, filled={}, required={"user"})
            >>> assert section.ready() is False
        """
        return not bool(self.required)

    def unwrap(self) -> dict[str, str]:
        """Unwraps `PartialSection` into mapping of string to string.

        Unwrapping is a main mechanism of `PartialSection` class. It allows to defer
        evaluation of some fields and also allows to require to have some specified
        fields. This method always throw an exception when unready. That means
        that this method can be safely used on request making.

        Examples:
            >>> import time
            >>>
            >>>
            >>> section = PartialSection(automatic={"time": lambda: str(time.time())},
            >>>                          filled={},
            >>>                          required={"user"})
            >>> # parameters = section.unwrap()  # Throws an error
            >>> section.update(PartialSection(automatic={"user": lambda: "Helltraitor"},
            >>>                                  filled={},
            >>>                                  required=set()))
            >>> parameters = section.unwrap()  # All is fine

        Returns:
            Mapping of string to string. Keys are mean the same as in a dictionary
            that provided on request making stage. For example, section can contain
            automatic time field that will be prepared just in time.

        Raises:
            RuntimeError: When section is not ready to be unwrapped.
        """
        if self.required:
            Logger.error("Unable to unwrap unready section with required fields %s",
                         self.required)
            raise RuntimeError(f"Required field are not satisfied: {self.required}")
        return self.filled | {key: fab() for key, fab in self.automatic.items()}

    def update(self, other: Self) -> None:
        """Updates this instance via another instance fields.

        This method is a way to update section with tracking required fields.
        Each updating may reduce required fields.

        Examples:
            >>> import time
            >>>
            >>>
            >>> section = PartialSection(automatic={},
            >>>                          filled={},
            >>>                          required={"user"})
            >>> # parameters = section.unwrap()  # Throws an error
            >>> section.update(PartialSection(automatic={"user": lambda: "Helltraitor"},
            >>>                                  filled={},
            >>>                                  required=set()))
            >>> parameters = section.unwrap()  # All is fine
        """
        self.automatic |= other.automatic
        self.filled |= other.filled

        self.required = self.required.union(other.required)
        self.required -= self.automatic.keys() | other.automatic.keys()
        self.required -= self.filled.keys() | other.filled.keys()
