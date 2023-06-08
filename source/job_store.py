import logging
from typing import Any

import telegram
from apscheduler.job import Job as APSJob, Job
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from telegram.ext import Job, Application, CallbackContext

logger = logging.getLogger(__name__)


class PTBSQLAlchemyJobStoreV20(SQLAlchemyJobStore):
    """
    Wraps apscheduler.SQLAlchemyJobStore to make :class:`telegram.ext.Job` class storable.
    """

    def __init__(self, application: Application, **kwargs: Any) -> None:
        if "url" in kwargs and kwargs["url"].startswith("sqlite:///"):
            logger.warning(
                "Use of SQLite db is not supported  due to "
                "multi-threading limitations of SQLite databases "
                "You can still try to use it, but it will likely "
                "behave differently from what you expect."
            )

        super().__init__(**kwargs)
        self._application = application

    def add_job(self, job: APSJob) -> None:
        job = self._prepare_job(job)
        super().add_job(job)

    def update_job(self, job: APSJob) -> None:
        job = self._prepare_job(job)
        super().update_job(job)

    @staticmethod
    def _prepare_job(job: APSJob) -> APSJob:
        prepped_job = APSJob.__new__(APSJob)
        prepped_job.__setstate__(job.__getstate__())
        if (isinstance(prepped_job.args, tuple)
                and len(prepped_job.args) > 0
                and isinstance(prepped_job.args[0], Job)):
            j: Job = prepped_job.args[0]
            prepped_job.args = (j.name, j.data, j.chat_id, j.user_id, j.callback)
        else:
            prepped_job.args = tuple()
        return prepped_job

    def _reconstitute_job(self, job_state: bytes) -> APSJob:
        job: APSJob = super()._reconstitute_job(job_state)

        if isinstance(job.args, tuple) and len(job.args) == 5:
            (name, data, chat_id, user_id, callback) = job.args

            tg_job: Job = telegram.ext.Job(
                callback=callback,
                name=name,
                data=data,
                chat_id=chat_id,
                user_id=user_id
            )

            job._modify(func=tg_job.run, args=(self._application,))
            tg_job._job = job
        return job
