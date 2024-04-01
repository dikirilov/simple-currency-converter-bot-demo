from __future__ import annotations
from datetime import datetime
import uuid
from models.currency import Currency
import sys
from loguru import logger


logger.remove()
logger.add(sys.stdout, level="TRACE", format="<green>{time}</green> | <blue>{module}</blue> | <lvl>{level}</lvl> | "
                                             "{message}", serialize=False)


class Currency2RubRate:
    def __init__(self,
                 curr: Currency,
                 rate: float
                 ):
        self.__id = str(uuid.uuid4())
        self.__curr : Currency = curr
        self.__rate : float = rate
        self.__created_at = datetime.now()
        self.__updated_at = datetime.now()

    @property
    def id(self):
        return self.__id

    @property
    def curr(self):
        return self.__curr

    @property
    def rate(self):
        return self.__rate

    @rate.setter
    def rate(self, rate):
        self.__rate = rate

    @property
    def created_at(self):
        return self.__created_at

    @property
    def updated_at(self):
        return self.__updated_at

    @updated_at.setter
    def updated_at(self, updated_at):
        self.__updated_at = updated_at

    def __repr__(self):
        return f"{self.__class__.__name__}({self.curr.symbol}, rate={self.rate})"
