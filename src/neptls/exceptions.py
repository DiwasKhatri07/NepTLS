"""NepTLS exception hierarchy."""


class NepTLSError(Exception):
    """Base class for all NepTLS errors."""


class RequestError(NepTLSError):
    """A network request could not be completed."""


class TransportUnavailableError(RequestError):
    """The requested optional HTTP transport is not installed or supported."""


class TimeoutError(RequestError):
    """A request exceeded its configured timeout."""


class HTTPStatusError(RequestError):
    """The server returned an unsuccessful HTTP status."""

    def __init__(self, message: str, response: object) -> None:
        super().__init__(message)
        self.response = response


class InvalidProfileError(NepTLSError):
    """A browser or TLS profile is invalid."""


class PowError(NepTLSError):
    """A proof-of-work challenge is invalid or unsolved."""
