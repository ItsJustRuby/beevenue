import re
from datetime import timedelta
from math import ceil
import re
import subprocess


def _get_timedelta(ffmpeg_stderr: str) -> timedelta:
    """Try to parse ffmpeg output of video length into a timedelta.

    Raises on error."""

    line_regex = re.compile(
        r".*Duration: (?P<hours>..):(?P<minutes>..)"
        r":(?P<seconds>..).(?P<centiseconds>..),"
    )

    for line in ffmpeg_stderr.splitlines():
        match = line_regex.match(line)
        if not match:
            continue

        delta = timedelta(
            hours=int(match.group("hours")),
            minutes=int(match.group("minutes")),
            seconds=int(match.group("seconds")),
            milliseconds=10 * int(match.group("centiseconds")),
        )
        return delta

    raise Exception("Could not determine length of video")


def get_length_in_ms(in_path: str) -> int:
    """Determine the length in seconds (rounded up) of the specified file."""

    cmd = [
        "ffmpeg",
        "-i",
        f"{in_path}",
        "-map",
        "0:v:0",
        "-c",
        "copy",
        "-f",
        "null",
        "-",
    ]

    completed_process = subprocess.run(
        cmd,
        encoding="utf-8",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )

    delta = _get_timedelta(completed_process.stderr)
    milliseconds = ceil(delta / timedelta(milliseconds=1))
    return milliseconds
