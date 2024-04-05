from models.currency_rate import Currency2RubRate
from models.currency import Currency
from typing import Iterable, Protocol
import xml.etree.ElementTree as ET
import aiohttp
import os
from loguru import logger
import sys


logger.remove()
logger.add(sys.stdout, level="TRACE", format="<green>{time}</green> | <blue>{module}</blue> | <lvl>{level}</lvl> | "
                                             "{message}", serialize=False)
URL = os.getenv("URL")
TIMEOUT = int(os.getenv("TIMEOUT"))


class CurrencyUpdater(Protocol):
    @classmethod
    async def get_currency_rates(cls) -> Iterable[Currency2RubRate]:
        raise NotImplementedError


class CurrencyUpdaterCBRF(CurrencyUpdater):
    URL = URL
    TIMEOUT = TIMEOUT

    @classmethod
    async def get_currency_rates(cls) -> Iterable[Currency2RubRate]:
        """
        A function that fetches currency exchange rates and returns a list of Currency2RubRate objects

        It utilizes aiohttp library to make requests to the CBRF API and parse gathered XML.
        """
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(cls.TIMEOUT)) as session:
            async with session.get(cls.URL) as response:
                logger.trace(f"Request to '{URL}':\nstatus is {response.status}")
                xml = await response.text()
        logger.trace(f"{xml=}")
        root_data = ET.fromstring(xml)
        res = []
        for curr in root_data:
            for element in curr:
                if element.tag == "Name":
                    name = element.text
                elif element.tag == "CharCode":
                    symbol = element.text
                elif element.tag == "NumCode":
                    code = int(element.text)
                elif element.tag == "VunitRate":
                    rate = float(element.text.replace(',', '.'))
            res.append(Currency2RubRate(Currency(name, symbol, code), rate))
        return res
