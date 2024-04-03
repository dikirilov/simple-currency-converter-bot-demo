import os

from business_layer.ptb_scheduler import PTBScheduler
from presentation_layer.telegram_ui import TelegramBot
from business_layer.converter import Converter
from business_layer.currency_updater import CurrencyUpdaterCBRF


def main():
    converter = Converter(CurrencyUpdaterCBRF())
    subscriber = PTBScheduler()
    ui = TelegramBot(converter=converter, token=os.getenv("TOKEN"), botname=os.getenv("BOTNAME"), subscriber=subscriber)
    ui.run()


if __name__ == "__main__":
    main()