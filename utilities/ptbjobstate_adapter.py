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
        """
        Initializes the class with the given application, callback function, and additional keyword arguments.

        As the class is more like a mixin, it is needed to call the __init__ method of the super class even though the
        class itself is not inherited.

        Parameters:
            application (Application): The application instance to be associated with the class.
            callback_func (Any): The callback function to be stored in the class.
            **kwargs (Any): Additional keyword arguments to be passed to the super class.
        """
        self.app = application
        self.callback_func = callback_func
        super().__init__(**kwargs)

    @staticmethod
    def _make_serializable(job: APSJob):
        """
        A method to convert an APSJob object into a serializable APSJob object which is needed due to the way
        PTB job utilizes APSJob.
        Takes a job of type APSJob as input and returns a serializable APSJob object.

        The callback function of APSJob is the same for all jobs (as designed by PTB jobstore).
        The callback function of PTBJob is the same for all jobs (as decided for this project).
        """
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
        """
        Restores a PTB job by creating a new PTBJob instance and modifying the original job's args.

        Utilizes self.app to get PTB jobqueue and self.callback_func to get the callback function.

        Args:
            job (APSJob): The APSJob to be restored.

        Returns:
            APSJob: The restored APSJob.
        """
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
