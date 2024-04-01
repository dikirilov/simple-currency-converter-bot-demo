from loguru import logger
import sys
from apscheduler.util import ref_to_obj, obj_to_ref
from apscheduler.job import Job as APSJob
from telegram.ext import Job as PTBJob, Application


logger.remove()
logger.add(sys.stdout, level="TRACE", format="<green>{time}</green> | <blue>{module}</blue> | <lvl>{level}</lvl> | {message}",
           serialize=False)


class PTBJobStateAdapter:
    def __init__(self, application: Application):
        self.app = application

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
            obj_to_ref(ptb_job.callback),
        )
        return serializable_apsjob

    def _restore_ptbjob(self, job: APSJob) -> APSJob:
        name, data, chat_id, user_id, callback_ref = job.args
        callback = ref_to_obj(callback_ref)

        ptb_job = self.app.job_queue.run_custom(callback, data=data, name=name, chat_id=chat_id, user_id=user_id,
                                                job_kwargs={})
        job.modify(args=(self.app.job_queue, ptb_job))
        return job
