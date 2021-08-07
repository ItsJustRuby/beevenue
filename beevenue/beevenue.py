"""Application factory. Lots of initial setup is performed here."""

from beevenue.types import BeevenueFlask
import logging
from typing import Any, Callable

from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from .auth.auth import init as auth_init_app
from .auth.routes import blueprint as auth_bp
from .cli import init_cli
from .core import batch_routes, stats_routes, media_routes, routes, tag_routes
from .db import db
from .db_init import init_app as db_init_app
from .flask import BeevenueFlaskImpl
from .init import init_app as context_init_app
from .login_manager import login_manager
from .principal import principal
from .fast.init import init_app as fast_init_app
from .strawberry.init import init_app as strawberry_init_app


def _nop(*_: Any) -> None:
    """Do nothing, intentionally."""


def get_application(
    fill_db: Callable[[BeevenueFlask, SQLAlchemy], None] = _nop,
) -> BeevenueFlask:
    """Construct and return uWSGI application object."""
    logging.basicConfig(level=logging.DEBUG)

    application = BeevenueFlaskImpl("beevenue-main", "0.0.0.0", 7000)
    application.config.from_envvar("BEEVENUE_CONFIG_FILE")

    CORS(
        application,
        supports_credentials=True,
        origins=application.config["BEEVENUE_ALLOWED_CORS_ORIGINS"],
    )

    db.init_app(application)
    Migrate(application, db)

    sentry_sdk.init(  # pylint: disable=abstract-class-instantiated
        dsn=application.config["SENTRY_DSN"],
        integrations=[FlaskIntegration(), SqlalchemyIntegration()],
        environment=application.config.get("SENTRY_ENVIRONMENT", "production"),
        traces_sample_rate=application.config.get(
            "SENTRY_TRACES_SAMPLE_RATE", 0.0
        ),
    )

    with application.app_context():
        login_manager.init_app(application)
        principal.init_app(application)
        context_init_app(application)
        db_init_app(application)

        application.register_blueprint(auth_bp)
        application.register_blueprint(routes.bp)
        application.register_blueprint(tag_routes.bp)
        application.register_blueprint(batch_routes.bp)
        application.register_blueprint(media_routes.bp)
        application.register_blueprint(stats_routes.bp)

        strawberry_init_app(application)

        # Only used for testing - needs to happen after DB is setup,
        # but before filling caches from DB.
        fill_db(application, db)

        fast_init_app(application)

    init_cli(application)
    auth_init_app()

    return application
