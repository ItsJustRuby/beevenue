from flask_sqlalchemy import SQLAlchemy

db: SQLAlchemy = SQLAlchemy(
    engine_options={
        "future": True,
    },
    session_options={"future": True},
)
