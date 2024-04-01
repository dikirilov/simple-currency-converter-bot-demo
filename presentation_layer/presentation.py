from typing import Protocol
from loguru import logger
import sys


logger.remove()
logger.add(sys.stdout, level="TRACE", format="<green>{time}</green> | <blue>{module}</blue> | <lvl>{level}</lvl> | "
                                             "{message}", serialize=False)


class Ui(Protocol):
    def run(self) -> None:
        raise NotImplementedError