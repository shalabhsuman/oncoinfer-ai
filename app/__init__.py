from pathlib import Path

from flask import Flask

from app.config import Config
from app.routes import register_routes


def create_app() -> Flask:
    base_dir = Path(__file__).resolve().parent.parent
    flask_app = Flask(
        __name__,
        template_folder=str(base_dir / "templates"),
        static_folder=str(base_dir / "static"),
    )
    flask_app.config.from_object(Config)
    register_routes(flask_app)
    return flask_app
