from __future__ import annotations
from datetime import datetime
import uuid
from typing import Optional
from models.currency_rate import Currency2RubRate
import sys
from loguru import logger


logger.remove()
logger.add(sys.stdout, level="TRACE", format="<green>{time}</green> | <blue>{module}</blue> | <lvl>{level}</lvl> | "
                                             "{message}", serialize=False)


class ConvertedQuery:
    def __init__(self,
                 curr_rate: Currency2RubRate,
                 amount: float,
                 query: Optional[str] = None,
                 ):
        """
        Initialize a new CurrencyConverter object.

        Constructs a query in case it's not provided.

        :param curr_rate (Currency2RubRate): The currency to ruble exchange rate object.
        :param amount (float): The amount of currency to convert.
        :param query (Optional[str], optional): A string query. Defaults to None.
        """
        self.__id = str(uuid.uuid4())
        self.__curr_rate = curr_rate
        self.__amount = amount
        self.__converted_amount = self.__amount * curr_rate.rate
        if query is None:
            self.__query = self.query_constructor()
        else:
            self.__query = query
        self.__created_at = datetime.now()
        self.__updated_at = datetime.now()

    def query_constructor(self):
        """
        A method that constructs a query using the amount and currency symbol.

        Returns:
        - A string representing the amount and currency symbol.
        """
        return f"{self.__amount} {self.__curr_rate.curr.symbol}"

    @property
    def id(self):
        return self.__id

    @property
    def query(self):
        return self.__query

    @property
    def original_amount(self):
        return self.__amount

    @property
    def converted_amount(self):
        return self.__converted_amount

    @property
    def curr_rate(self):
        return self.__curr_rate

    def __repr__(self):
        return f"{self.__class__.__name__}({self.query})"