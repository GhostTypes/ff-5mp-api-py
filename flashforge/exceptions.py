"""
FlashForge Python API - Exceptions
"""

from __future__ import annotations


class FlashForgeError(Exception):
    """Base class for every error this library raises deliberately."""


class FlashForgeResponseError(FlashForgeError):
    """
    The printer answered, but the payload could not be understood.

    This is deliberately distinct from a ``None`` return, which every HTTP
    control method uses for "could not reach the printer / the printer refused
    us". Collapsing the two is what made ff-5mp-hass#18 take three releases to
    diagnose: a Creator 5 reporting ``chamberTemp: -108`` (the firmware's "no
    chamber sensor" sentinel) surfaced in Home Assistant as ``cannot_connect``,
    pointing the user at their network for a schema problem.

    Raise this whenever the transport succeeded and the *content* was the
    problem, so callers can tell the user something actionable.
    """

    def __init__(
        self,
        message: str,
        *,
        endpoint: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """
        Args:
            message: Human-readable description of what could not be parsed.
            endpoint: The endpoint whose response failed, e.g. "/detail".
            cause: The underlying validation/decode error, kept for logs.
        """
        super().__init__(message)
        self.message = message
        self.endpoint = endpoint
        self.cause = cause

    def __str__(self) -> str:
        parts = [self.message]
        if self.endpoint:
            parts.append(f"(endpoint: {self.endpoint})")
        if self.cause:
            parts.append(f"caused by {type(self.cause).__name__}: {self.cause}")
        return " ".join(parts)
