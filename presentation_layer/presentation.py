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


class Ui(Protocol):
    async def run(self) -> None:
        raise NotImplementedError