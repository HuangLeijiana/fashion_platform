from __future__ import annotations

from celery import Celery

from app import create_app


def make_celery() -> Celery:
    flask_app = create_app()
    celery_app = Celery(
        flask_app.import_name,
        broker=flask_app.config.get("CELERY_BROKER_URL"),
        backend=flask_app.config.get("CELERY_RESULT_BACKEND"),
    )
    celery_app.conf.update(flask_app.config)

    class FlaskTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = FlaskTask
    return celery_app


celery_app = make_celery()


@celery_app.task(name="advisor.reindex_knowledge_base")
def reindex_knowledge_base_task(force: bool = False) -> int:
    from app.services.vector_store import index_knowledge_base

    return index_knowledge_base(force=force)


@celery_app.task(name="advisor.reindex_user_wardrobe")
def reindex_user_wardrobe_task(user_id: str) -> int:
    from app.services.vector_store import index_user_wardrobe

    return index_user_wardrobe(user_id)