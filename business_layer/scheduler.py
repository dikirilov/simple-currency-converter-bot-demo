from telegram.ext import Application
from typing import Protocol
import sys
from loguru import logger


logger.remove()
logger.add(sys.stdout, level="TRACE", format="<green>{time}</green> | <blue>{module}</blue> | <lvl>{level}</lvl> | "
                                             "{message}", serialize=False)


class Scheduler(Protocol):
    def __init__(self):
        self.cmd_sub_label = "subscribe"
        self.cmd_unsub_label = "unsubscribe"
        self._notify_func = None
        self.cmds = {
            self.cmd_sub_label: self.subscribe,
            self.cmd_unsub_label: self.unsubscribe
        }

    async def adjust_tg(self, app: Application, **kwargs) -> None:
        pass

    def set_callback(self, notify_func):
        self._notify_func = notify_func

    def create_inline_keyboard_sub(self, **kwargs) -> object:
        raise NotImplementedError

    def create_inline_keyboard_unsub(self, **kwargs) -> object:
        raise NotImplementedError

    async def subscribe(self, subscription_meta: dict, context: object) -> bool:
        raise NotImplementedError

    async def unsubscribe(self, subscription_meta: dict, context: object) -> bool:
        raise NotImplementedError

