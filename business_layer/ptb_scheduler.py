import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, Application
from business_layer.scheduler import Scheduler
from utilities.custom_jobstore import PTBJobStore
import sys
from loguru import logger


logger.remove()
logger.add(sys.stdout, level="TRACE", format="<green>{time}</green> | <blue>{module}</blue> | <lvl>{level}</lvl> | "
                                             "{message}", serialize=False)
PSQL_URL = os.getenv("PSQL_URL")
JOB_PERSISTENCE = int(os.getenv("JOB_PERSISTENCE", 0))


class PTBScheduler(Scheduler):
    def __init__(self):
        super().__init__()
        self.subscription_plans = {
            "daily": {"label": "Ежедневно", "interval": 60*60*24},
            "weekly": {"label": "Еженедельно", "interval": 60*60*24*7},
            "monthly": {"label": "Ежемесячно", "interval": 60*60*24*30}
        }

    def create_inline_keyboard_sub(self, **kwargs) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"Подписаться на обновления ({dct['label'].lower()})",
                    callback_data=
                    {
                        "cmd": self.cmd_sub_label,
                        "type": key,
                        **kwargs
                    },
                )
            ]
            for key, dct in self.subscription_plans.items()
        ])

    def create_inline_keyboard_unsub(self, **kwargs) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "Отписаться от обновлений",
                    callback_data={
                        "cmd": self.cmd_unsub_label,
                        **kwargs
                    },
                )
            ]
        ])

    async def create_callback_data(self):
        pass

    async def notify(self, *args, **kwargs):
        logger.trace(f"notify from ptb_subscriber had been called, args: {args}, kwargs: {kwargs}")
        await self._notify_func(*args, **kwargs)

    def adjust_tg(self, app: Application, callback_func, **kwargs):
        if JOB_PERSISTENCE > 0:
            logger.trace(f"Adding PTBJobStore, {PSQL_URL=}")
            app.job_queue.scheduler.add_jobstore(
                PTBJobStore(application=app, callback_func=callback_func, url=PSQL_URL),
            )
            logger.trace(f"{app.job_queue.scheduler._jobstores=}")

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        subscription_meta = update.callback_query.data
        logger.trace(f"{subscription_meta=}")
        type = subscription_meta["type"]
        chat_id = subscription_meta.get("chat_id", None)
        if chat_id is None:
            logger.error(f"Chat id is not specified within subscription meta")
            return False
        if self.subscription_plans.get(type, None) is None:
            logger.error(f"Unknown subscription type: {type}")
            return False
        if subscription_meta.get("data_for_scheduler", None):
            data = subscription_meta["data_for_scheduler"]
        else:
            if subscription_meta.get("query", None):
                logger.warning(f"Data for scheduler is not specified within subscription meta, but query is specified, "
                               f"so it will be used")
                data = subscription_meta["query"]
            else:
                logger.error(f"Data for scheduler is not specified within subscription meta and query is not specified")
                return False

        context.application.job_queue.run_repeating(self.notify, self.subscription_plans[type]["interval"],
                                                    data=data,
                                                    chat_id=chat_id,
                                                    name=str(chat_id))
        return True

    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        subscription_meta = update.callback_query.data
        chat_id = subscription_meta.get("chat_id", None)
        if chat_id is None:
            logger.error(f"Chat id is not specified within subscription meta")
            return False
        job_name = str(chat_id)
        job = context.application.job_queue.get_jobs_by_name(job_name)[0]
        if job:
            job.schedule_removal()
            return True
        else:
            logger.error(f"Job with name {job_name} is not found")
            return False

