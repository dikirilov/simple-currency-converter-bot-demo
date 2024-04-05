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
        """
        Initializes the PTBJobStore instance with the given application and optional keyword arguments.

        Parameters:
            application (Application): The application instance.
            **kwargs (Any): Optional keyword arguments.
        """
        logger.trace(f"init {self.__class__.__name__} with kwargs: {kwargs}")
        super(PTBJobStore, self).__init__(application, **kwargs)

    def add_job(self, job: APSJob) -> None:
        """
        A method to add a job to the job queue.
        This is a modified version of the add_job method in the SQLAlchemyJobStore class to add PTB job support.

        Parameters:
            job (APSJob): The job to be added to the queue.
        """
        job = self._make_serializable(job)
        super().add_job(job)

    def update_job(self, job: APSJob) -> None:
        """
        A method to update a job in the job queue.

        This is a modified version of the update_job method in the SQLAlchemyJobStore class to add PTB job support.

        Parameters:
            job (APSJob): The job to be updated.
        """
        job = self._make_serializable(job)
        super().update_job(job)

    def _reconstitute_job(self, job_state: bytes) -> APSJob:
        """
        A method to recreate a job in the job queue from its state.

        This is a modified version of the _reconstitute_job method in the SQLAlchemyJobStore class to add PTB job support.

        Parameters:
            job_state (bytes): The state of the job to be reconstituted.
        """
        job: APSJob = super()._reconstitute_job(job_state)  # pylint: disable=W0212
        return super()._restore_ptbjob(job)