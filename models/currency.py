from __future__ import annotations
from datetime import datetime
from typing import Optional
import uuid
import sys
from loguru import logger


logger.remove()
logger.add(sys.stdout, level="TRACE", format="<green>{time}</green> | <blue>{module}</blue> | <lvl>{level}</lvl> | "
                                             "{message}", serialize=False)


class Currency:
    def __init__(self,
                 name: str,
                 symbol: str,
                 code: Optional[int] = None,
                 ):
        """
        Constructor for initializing the class with the given parameters.

        :param name (str): The name of the object.
        :param symbol (str): The symbol representing the object.
        :param code (int, optional): The code associated with the object. Defaults to None.
        """
        self.__id = uuid.uuid4()
        self._name = name
        self._symbol = symbol
        self._code = code
        self.__created_at = datetime.now()
        self.__updated_at = datetime.now()

    @property
    def id(self):
        return self.__id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(self, symbol):
        self._symbol = symbol

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, code):
        self._code = code

    def __eq__(self, other):
        return self._code == other.code

    @property
    def created_at(self):
        return self.__created_at

    @property
    def updated_at(self):
        return self.__updated_at
