import os

from presentation_layer.console import Console
from presentation_layer.telegram_ui import TelegramBot
from business_layer.converter import Converter
from business_layer.currency_updater import CurrencyUpdaterCBRF
import asyncio


def main():
    converter = Converter(CurrencyUpdaterCBRF())
    # ui = Console(converter)
    ui = TelegramBot(converter, token=os.getenv("TOKEN"), botname=os.getenv("BOTNAME"))
    ui.run()


if __name__ == "__main__":
    main()