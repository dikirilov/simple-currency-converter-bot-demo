import re
from business_layer.currency_updater import CurrencyUpdater
from datetime import datetime
from models.currency_rate import Currency2RubRate
from models.converted_query import ConvertedQuery
from typing import Any, Iterable
import os
import sys
from loguru import logger


logger.remove()
logger.add(sys.stdout, level="TRACE", format="<green>{time}</green> | <blue>{module}</blue> | <lvl>{level}</lvl> | "
                                             "{message}", serialize=False)
REGEXP = os.getenv("REGEXP")


class Converter:
    def __init__(self, updater: CurrencyUpdater):
        """
        Initializes the CurrencyUpdater object with the provided updater.

        :param updater (CurrencyUpdater): The CurrencyUpdater object to be initialized with.

        :returns None
        """
        self.regexp = REGEXP
        self.updater: CurrencyUpdater = updater
        self.update_dt = None
        self.matching = {}
        self.currency_rates = []

    async def update_rates(self):
        """
        Updates the rates utilizing updater object.

        self.matching dict is calculated straight away based on the updated rates.
        """
        self.update_dt = datetime.today()
        self.matching = {'name': {}, 'code': {}, 'symbol': {}}
        self.currency_rates = await self.updater.get_currency_rates()
        for curr_rate in self.currency_rates:
            self.matching['name'][curr_rate.curr.name.lower()] = curr_rate
            self.matching['symbol'][curr_rate.curr.symbol.lower()] = curr_rate

    async def match_curr(self, requested_curr) -> Iterable[Currency2RubRate] | None:
        """
        A function to match the requested currency with the available currency rates.
        :param requested_curr: The currency to be matched.

        The matching is based on the currency code and name.

        Returns:
            An iterable of Currency2RubRate if there is a match, otherwise None.
        """
        curr = requested_curr.lower()
        matched = []
        if self.update_dt is None:
            await self.update_rates()
        if (datetime.today() - self.update_dt).days >= 1:
            await self.update_rates()
        for key in self.matching.keys():
            if curr in self.matching[key]:
                matched.append(self.matching[key][curr])
                continue
            for label in self.matching[key]:
                if label.find(curr) != -1:
                    matched.append(self.matching[key][label])
        if len(matched) > 0:
            return matched
        return None

    async def parse_request(self, request: Any) -> Iterable[ConvertedQuery]:
        """
        A function that parses a request and returns an iterable of ConvertedQuery objects.

        Parses based on the assumption that request is in the form of:
        '<amount> <currency>'

        Amount could be an expression, but it shouldn't have spaces inside.

        It is also possible that amount is not provided (so, no spaces in the request), in which case
        it will be assumed to be 1.

        Args:
            self: The object instance
            request (Any): The request to be parsed
        Returns:
            Iterable[ConvertedQuery]: An iterable of ConvertedQuery objects
        Raises:
            ValueError: If the request is None, not a string, or if certain conditions are not met
        """
        if request is None:
            raise ValueError("Request cannot be empty")
        if not isinstance(request, str):
            raise ValueError("Request must be a string")
        req_params = []
        req_params.extend(map(str.strip, request.split()))
        if len(req_params) > 1:
            expr, currency_marker = req_params
        else:
            currency_marker = req_params[0]
            expr = "1"
        amount = await self.parse_expression(expr)
        if currency_marker is None or currency_marker == "":
            raise ValueError(f"Currency is not recognized (empty): '{currency_marker}'")
        if currs := await self.match_curr(currency_marker):
            return [ConvertedQuery(curr_rate, amount) for curr_rate in currs]
        else:
            raise ValueError(f"Currency '{currency_marker}' is not recognized")

    async def parse_expression(self, expression: str) -> float:
        """
        A function that parses the given expression and returns the result as a float.

        The parsing is based on a regular expression which is intended to check if the expression
        is valid (could be evaluated)

        Args:
            expression (str): The expression to be parsed.

        Returns:
            float: The result of the parsed expression.
        """
        regexp = self.regexp
        if not re.match(regexp, expression):
            raise ValueError(f"Invalid expression: '{expression}'")
        if expression.startswith("/") or expression.startswith("*"):
            raise ValueError(f"Invalid expression: '{expression}'")
        logger.trace(f"Expression '{expression}' is valid")
        return float(eval(expression))