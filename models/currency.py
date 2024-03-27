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
                 match_expressions: Optional[list] = None
                 ):
        self.__id = uuid.uuid4()
        self._name = name
        self._symbol = symbol
        self._code = code
        if match_expressions is None:
            self._match_expressions = [code, name, symbol]
        else:
            self._match_expressions = match_expressions
            self._match_expressions.extend([code, name, symbol])
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
    def match_expressions(self):
        return self._match_expressions

    @match_expressions.setter
    def match_expressions(self, match_expressions):
        self._match_expressions = match_expressions

    def append_match_expression(self, match_expression):
        self._match_expressions.append(match_expression)

    @property
    def created_at(self):
        return self.__created_at

    @property
    def updated_at(self):
        return self.__updated_at
