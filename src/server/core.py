import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from server.encoder import AlchemyEncoder
from server.pipeline import celery
from server.pipeline.demo import tasks as demo_tasks
from server.pipeline.demo.api import demo_api
from server.pipeline.simulation.api import simulation_api
from server.pipeline.simulation import tasks as simulation_tasks
from server.pipeline.simbad_cli import tasks as simbad_cli_task

from database import init_db, init_engine

logger = logging.getLogger()


def create_app(debug=False):
    return entrypoint(debug=debug, mode='app')


def create_celery(debug=False):
    return entrypoint(debug=debug, mode='celery')


def entrypoint(debug=False, mode='app'):
    assert isinstance(mode, str), 'bad mode type "{}"'.format(type(mode))
    assert mode in ('app', 'celery'), 'bad mode "{}"'.format(mode)

    app = Flask(__name__)
    app.debug = debug
    app.json_encoder = AlchemyEncoder
    configure_app(app)

    init_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    init_db()

    configure_logging(debug=debug)

    configure_celery(app, demo_tasks.celery)
    configure_celery(app, simulation_tasks.celery)
    configure_celery(app, simbad_cli_task.celery)

    # register blueprints
    app.register_blueprint(demo_api, url_prefix='/api')
    app.register_blueprint(simulation_api, url_prefix='/api')

    if mode == 'app':
        return app
    elif mode == 'celery':
        return celery


def configure_app(app):
    logger.info('configuring flask app')
    app.config.from_object('config.settings')


def configure_celery(app, celery):
    # set broker url and result backend from app config
    celery.conf.broker_url = app.config['CELERY_BROKER_URL']
    celery.conf.result_backend = app.config['CELERY_RESULT_BACKEND']

    # subclass task base for app context
    # http://flask.pocoo.org/docs/0.12/patterns/celery/
    task_base = celery.Task

    class AppContextTask(task_base):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return task_base.__call__(self, *args, **kwargs)

    celery.Task = AppContextTask

    # run finalize to process decorated tasks
    celery.finalize()


def configure_logging(debug=True):
    root = logging.getLogger()
    h = logging.StreamHandler()
    fmt = logging.Formatter(
        fmt='%(asctime)s %(levelname)s (%(name)s) %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    h.setFormatter(fmt)

    root.addHandler(h)

    if debug:
        root.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.INFO)
