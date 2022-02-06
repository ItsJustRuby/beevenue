from typing import NamedTuple, Union


class ErrorThumbnailingResult:
    """Thumbnailing was unsuccessful, error details are within."""

    def __init__(self, error: str) -> None:
        self.error = error


class SuccessThumbnailingResult:
    """Thumbnailing was successful."""

    def __init__(self) -> None:
        self.error = None


ThumbnailingResult = Union[ErrorThumbnailingResult, SuccessThumbnailingResult]


class Measurements(NamedTuple):
    """Tuple holding a medium's measurements to be stored later."""

    width: int
    height: int
    filesize: int
