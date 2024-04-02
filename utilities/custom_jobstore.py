from loguru import logger
import sys
from typing import Any
from apscheduler.job import Job as APSJob
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from utilities.ptbjobstate_adapter import PTBJobStateAdapter
from telegram.ext import Application


logger.remove()
logger.add(sys.stdout, level="TRACE", format="<green>{time}</green> | <blue>{module}</blue> | <lvl>{level}</lvl> | {message}",
           serialize=False)


class PTBJobStore(PTBJobStateAdapter, SQLAlchemyJobStore):
    def __init__(self, application: Application, **kwargs: Any) -> None:
        logger.trace(f"init {self.__class__.__name__} with kwargs: {kwargs}")
        super(PTBJobStore, self).__init__(application, **kwargs)

    def add_job(self, job: APSJob) -> None:
        job = self._make_serializable(job)
        super().add_job(job)

    def update_job(self, job: APSJob) -> None:
        job = self._make_serializable(job)
        super().update_job(job)

    def _reconstitute_job(self, job_state: bytes) -> APSJob:
        job: APSJob = super()._reconstitute_job(job_state)  # pylint: disable=W0212
        return super()._restore_ptbjob(job)