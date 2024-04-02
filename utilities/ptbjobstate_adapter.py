from loguru import logger
import sys
from typing import Any
from apscheduler.job import Job as APSJob
from telegram.ext import Job as PTBJob, Application


logger.remove()
logger.add(sys.stdout, level="TRACE", format="<green>{time}</green> | <blue>{module}</blue> | <lvl>{level}</lvl> | {message}",
           serialize=False)


class PTBJobStateAdapter:
    def __init__(self, application: Application, callback_func, **kwargs: Any):
        self.app = application
        self.callback_func = callback_func
        super().__init__(**kwargs)

    @staticmethod
    def _make_serializable(job: APSJob):
        serializable_apsjob = APSJob.__new__(APSJob)
        serializable_apsjob.__setstate__(job.__getstate__())
        ptb_job = PTBJob.from_aps_job(job)
        serializable_apsjob.args = (
            ptb_job.name,
            ptb_job.data,
            ptb_job.chat_id,
            ptb_job.user_id,
        )
        return serializable_apsjob

    def _restore_ptbjob(self, job: APSJob) -> APSJob:
        name, data, chat_id, user_id = job.args
        ptb_job = PTBJob(
            callback=self.callback_func,
            data=data,
            name=name,
            chat_id=chat_id,
            user_id=user_id,
        )
        job._modify(args=(self.app.job_queue, ptb_job))
        return job
