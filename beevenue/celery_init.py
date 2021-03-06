from typing import Any

from celery import Celery, Task
from beevenue.core.ffmpeg import generate_picks_task
from beevenue.core.ffmpeg.animated_thumbnails import generate_animated_task


def init_app(app: Any) -> None:
    celery = Celery(app.name, broker=app.config["CELERY_BROKER_URL"])
    celery.conf.update(app.config)

    class ContextTask(Task):  # pylint: disable=abstract-method
        """Custom Task class which pushes Flask's internal app_context()."""

        def __call__(self: Any, *args: Any, **kwargs: Any) -> Any:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    app.celery = celery

    @app.celery.task
    def gpt_helper(medium_id: int, in_path: str) -> None:
        generate_picks_task(medium_id, in_path)

    app.generate_picks_task = gpt_helper

    @app.celery.task
    def gat_helper(in_path: str, medium_hash: str) -> None:
        generate_animated_task(in_path, medium_hash)

    app.generate_animated_task = gat_helper
