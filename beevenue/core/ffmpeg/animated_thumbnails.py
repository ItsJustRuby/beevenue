from contextlib import AbstractContextManager
from datetime import timedelta
from distutils.log import debug
from math import inf
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from typing import Any, List

from flask import current_app

from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

from beevenue import paths

from .measure import get_length_in_ms


class _AnimatedThumbnailTemporaryDirectory(AbstractContextManager):
    def __init__(self) -> None:
        # The temporary dictionary we use needs to be local in order for
        # ffmpeg to feel safe operating in it.
        self.inner = TemporaryDirectory(dir=".")

    def filename(self, local_path: str) -> str:
        return str(Path(self.inner.name, local_path))

    def __exit__(self, exc: Any, value: Any, tb: Any) -> None:
        self.inner.__exit__(exc, value, tb)


def _detect_scenes(in_path: str) -> List[Any]:
    video_manager = VideoManager([in_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector())

    video_manager.set_downscale_factor()
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)

    return scene_manager.get_scene_list()  # type: ignore


def _pick_scenes(scene_list: List[Any], length_in_ms: int, N: int) -> List[Any]:
    scenes_ms = []
    for scene in scene_list:
        scenes_ms.append(scene[0].get_seconds() * 1000)

    # drop N regular pins on a timeline, rounding to the
    # nearest frame where a scene starts
    scene_indices = set()
    last_scene_index = 0

    step_size_ms = length_in_ms / N
    for step_index in range(0, N):
        step_starting_ms = (step_index + 1) * (step_size_ms)

        best_scene_diff = inf
        current_scene_index = last_scene_index
        best_scene_index = last_scene_index
        for scene_ms in scenes_ms[last_scene_index:]:
            current_diff = abs(scene_ms - step_starting_ms)
            if current_diff < best_scene_diff:
                best_scene_diff = current_diff
                best_scene_index = current_scene_index
            else:
                continue
            current_scene_index += 1

        scene_indices.add(best_scene_index)

    # omit all duplicate pins
    sorted_scene_indices = sorted(scene_indices)
    best_scenes = [scene_list[s] for s in sorted_scene_indices]

    return best_scenes


def _entire(in_path: str, medium_hash: str) -> None:
    for thumbnail_size, thumbnail_size_pixels in current_app.config[
        "BEEVENUE_THUMBNAIL_SIZES"
    ].items():
        target_path = paths.thumbnail_path(
            medium_hash, thumbnail_size, is_animated=True
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            f"{in_path}",
            "-vf",
            f"scale={thumbnail_size_pixels}:-2",
            "-an",  # mute the audio
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            target_path,
        ]

        debug("".join(cmd))
        completed_process = subprocess.run(
            cmd,
            encoding="utf-8",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
        debug(completed_process.stderr)


def generate_animated(in_path: str, medium_hash: str) -> None:
    current_app.generate_animated_task.delay(in_path, medium_hash)  # type: ignore


def generate_animated_task(in_path: str, medium_hash: str) -> None:
    slice_count = 5
    slice_length = 5  # seconds

    if in_path.endswith(".gif"):
        _entire(in_path, medium_hash)
        return

    length_in_ms = get_length_in_ms(in_path)

    if length_in_ms < 1000 * slice_count * slice_length:
        _entire(in_path, medium_hash)
        return

    # run scene detection, get frame indices of scenes.
    # Each returned scene is a tuple of the (start, end) timecode.
    scene_list = _detect_scenes(in_path)
    best_scenes = _pick_scenes(scene_list, length_in_ms, slice_count)

    # pick K seconds starting at each pin
    for thumbnail_size, thumbnail_size_pixels in current_app.config[
        "BEEVENUE_THUMBNAIL_SIZES"
    ].items():
        with _AnimatedThumbnailTemporaryDirectory() as dir:
            i = 0
            for scene in best_scenes:
                scene_length_in_milliseconds = (
                    scene[1] - scene[0]
                ).get_seconds() * 1000
                if scene_length_in_milliseconds < slice_length * 1000:
                    trim_in_milliseconds = scene_length_in_milliseconds
                else:
                    trim_in_milliseconds = slice_length * 1000

                delta = timedelta(milliseconds=trim_in_milliseconds)

                cmd = [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    scene[0].get_timecode(),
                    "-i",
                    f"{in_path}",
                    "-vf",
                    f"scale={thumbnail_size_pixels}:-2",
                    "-an",  # mute the audio
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-t",
                    str(delta),
                    dir.filename(f"output_{i}.mp4"),
                ]

                completed_process = subprocess.run(
                    cmd,
                    encoding="utf-8",
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    check=False,
                )

                i += 1

            playlist_filename = dir.filename("temp.txt")
            with open(playlist_filename, "w") as plalist_file:
                for j in range(0, i):
                    filename = f"output_{j}.mp4"
                    plalist_file.write(f"file '{filename}'\n")

            # concatenate those into a video
            target_path = paths.thumbnail_path(
                medium_hash, thumbnail_size, is_animated=True
            )

            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-i",
                playlist_filename,
                "-c",
                "copy",
                target_path,
            ]
            debug("".join(cmd))
            completed_process = subprocess.run(
                cmd,
                encoding="utf-8",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                check=False,
            )
            debug(completed_process.stderr)
