from pathlib import Path
import re
from datetime import timedelta
from math import ceil, inf
from pathlib import Path
import re
import subprocess

from flask import current_app

from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

from beevenue import paths
from beevenue.flask import g
from ..interface import Measurements, ThumbnailingResult
from .image import image_thumbnails, measure as measure_image
from .temporary_thumbnails import temporary_thumbnails
from .measure import get_length_in_ms
from .video import video_thumbnails, measure as measure_video
from . import async_thumbnails


def measure(in_path: str, mime_type: str) -> Measurements:
    if re.match("image/", mime_type):
        return measure_image(in_path)
    if re.match("video/", mime_type):
        return measure_video(in_path)

    raise Exception(f"Cannot measure file with mime_type {mime_type}")


def thumbnails(
    in_path: str, extensionless_out_path: Path, mime_type: str
) -> ThumbnailingResult:
    """Generate and persist thumbnails of the file at ``in_path``."""

    if re.match("image/", mime_type):
        return image_thumbnails(in_path, extensionless_out_path)
    if re.match("video/", mime_type):
        return video_thumbnails(in_path, extensionless_out_path)

    raise Exception(f"Cannot create thumbnails for mime_type {mime_type}")


def _set_thumbnail(
    medium_hash: str, thumbnail_size: str, raw_bytes: bytes
) -> None:
    out_path = Path(paths.thumbnail_path(medium_hash, thumbnail_size))

    with open(out_path, "wb") as out_file:
        out_file.write(raw_bytes)

def generate_animated_task(medium_id, in_path: str) -> None:
    N = 3
    K = 3 # seconds

    length_in_ms = get_length_in_ms(in_path)

    if length_in_ms < 1000 * N * K:
        print("TODO: Just thumbnail the whole video")
        return 200

    video_manager = VideoManager([in_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(
        ContentDetector())

    # Improve processing speed by downscaling before processing.
    video_manager.set_downscale_factor()

    # Start the video manager and perform the scene detection.
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)

    # Each returned scene is a tuple of the (start, end) timecode.
    scene_list = scene_manager.get_scene_list()
    print(scene_list)

    scenes_ms = []
    for scene in scene_list:
        scenes_ms.append(scene[0].get_seconds() * 1000)

    # run scene detection, get frame indices of scenes.

    # drop N regular pins on a timeline, rounding to the nearest frame where a scene starts
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
    best_scenes = [scene_list[s][0] for s in sorted_scene_indices]

    print("Picked scene indices", sorted_scene_indices)
    print("Scenes", best_scenes)

    # pick K seconds starting at each pin
    for _, thumbnail_size_pixels in current_app.config[
        "BEEVENUE_THUMBNAIL_SIZES"
    ].items():
        i = 0
        for scene in best_scenes:
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                f"{in_path}",
                "-vf",
                f"scale={thumbnail_size_pixels}:-2",
                "-ss",
                scene.get_timecode(),
                "-an", # mute the audio
                "-c:v", "libx264" ,"-pix_fmt", "yuv420p",
                "-t",
                str(K),
                f"output_{i}.mp4"
            ]

            print(cmd)
            completed_process = subprocess.run(
                cmd, encoding="utf-8", stderr=subprocess.PIPE, check=False
            )
            print(completed_process.stderr)
            
            i += 1
        
        with open("temp.txt", "w") as f:
            for j in range(0, i):
                f.write(f"file 'output_{j}.mp4'\n")
            
        # concatenate those into a video
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-i",
            "temp.txt",
            "-c",
            "copy",
            f"all.mp4"
        ]
        completed_process = subprocess.run(
            cmd, encoding="utf-8", stderr=subprocess.PIPE, check=False
        )
        print(completed_process.stderr)

    return 200

def generate_picks_task(medium_id: int, in_path: str) -> None:
    """Generate some preview-sized thumbnails in-memory.

    The files are temporarily persisted (in redis)."""

    async_thumbnails.start_persisting(medium_id)

    all_thumbs = []

    for _, thumbnail_size_pixels in current_app.config[
        "BEEVENUE_THUMBNAIL_SIZES"
    ].items():
        with temporary_thumbnails(
            in_path, thumbnail_size_pixels
        ) as temporary_thumbs:
            for thumb_file_name in temporary_thumbs:
                with open(thumb_file_name, "rb") as thumb_file:
                    these_bytes = thumb_file.read()
                    all_thumbs.append(
                        (
                            thumbnail_size_pixels,
                            these_bytes,
                        )
                    )

    async_thumbnails.finish_persisting(medium_id, all_thumbs)


def generate_picks(medium_id: int, in_path: str) -> None:
    current_app.generate_picks_task.delay(medium_id, in_path)  # type: ignore


def generate_animated(medium_id: int, in_path: str) -> None:
    current_app.generate_animated_task.delay(medium_id, in_path)  # type: ignore


def pick(medium_id: int, index: int, medium_hash: str) -> None:
    """Pick ``index`` as the new thumbnail.

    Afterwards expires all temporary thumbnails for that medium."""

    for thumbnail_size, thumbnail_size_pixels in current_app.config[
        "BEEVENUE_THUMBNAIL_SIZES"
    ].items():
        thumb = async_thumbnails.pick(medium_id, thumbnail_size_pixels, index)
        if thumb:
            _set_thumbnail(medium_hash, thumbnail_size, thumb)

    async_thumbnails.cleanup(medium_id)
