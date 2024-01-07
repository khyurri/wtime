import pytest
from wtime import time_format


def test_format_seconds() -> None:
    formatted = time_format.seconds(100)
    assert formatted == "100s"


@pytest.mark.parametrize(
    "seconds,exp_format",
    [
        (61, "1m 1s"),
        (60, "1m 0s"),
    ],
)
def test_format_minutes(seconds: int, exp_format: str) -> None:
    assert time_format.minutes(seconds) == exp_format


@pytest.mark.parametrize(
    "seconds,exp_format",
    [
        (3601, "1h 0m 1s"),
        (3665, "1h 1m 5s"),
        (7199, "1h 59m 59s"),
        (7200, "2h 0m 0s"),
        (7201, "2h 0m 1s"),
    ],
)
def test_format_hours(seconds: int, exp_format: str) -> None:
    assert time_format.hours(seconds) == exp_format


@pytest.mark.parametrize(
    "seconds,exp_format",
    [
        (0, "0s"),
        (59, "59s"),
        (60, "1m 0s"),
        (3599, "59m 59s"),
        (3600, "1h 0m 0s"),
        (3601, "1h 0m 1s"),
    ],
)
def test_format(seconds: int, exp_format: str) -> None:
    assert time_format.format(seconds) == exp_format
