import os
from flask import Flask
from .config import Config, DevelopmentConfig, TestingConfig, ProductionConfig
from .models import db
from . import routes


def create_app(config_name=None):
    """Application Factory"""
    app = Flask(__name__, instance_relative_config=True)

    # Загрузка конфигурации
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    if config_name == 'testing':
        app.config.from_object(TestingConfig)
    elif config_name == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # Создание instance папки
    os.makedirs(app.instance_path, exist_ok=True)

    # Инициализация SQLAlchemy
    db.init_app(app)

    # Регистрация роутов
    routes.init_routes(app)

    return app