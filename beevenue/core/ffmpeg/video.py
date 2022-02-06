from pathlib import Path
import subprocess

from flask import current_app

from ..interface import (
    ErrorThumbnailingResult,
    SuccessThumbnailingResult,
    ThumbnailingResult,
    Measurements,
)


def measure(in_path: str) -> Measurements:
    filesize = Path(in_path).stat().st_size

    # ffprobe should return a CSV string such as "480,360" from this
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0",
        in_path,
    ]

    completed_process = subprocess.run(
        cmd, encoding="utf-8", stdout=subprocess.PIPE, check=False
    )

    two_strings = completed_process.stdout.strip().split(",")
    width = int(two_strings[0])
    height = int(two_strings[1])

    return Measurements(width=width, height=height, filesize=filesize)


def video_thumbnails(
    in_path: str, extensionless_out_path: Path
) -> ThumbnailingResult:
    for thumbnail_size, thumbnail_size_pixels in current_app.config[
        "BEEVENUE_THUMBNAIL_SIZES"
    ].items():
        min_axis = thumbnail_size_pixels
        out_path = extensionless_out_path.with_suffix(f".{thumbnail_size}.jpg")

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            f"{in_path}",
            "-vf",
            f"thumbnail,scale={min_axis}:-1",
            "-frames:v",
            "1",
            f"{out_path}",
        ]

        ffmpeg_result = subprocess.run(cmd, check=False)

        if ffmpeg_result.returncode != 0:
            return ErrorThumbnailingResult(
                "Could not create thumbnail for video."
            )

    return SuccessThumbnailingResult()
