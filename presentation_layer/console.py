import asyncio
from presentation_layer.presentation import Ui
from business_layer.converter import Converter
import sys
from loguru import logger


logger.remove()
logger.add(sys.stdout, level="TRACE", format="<green>{time}</green> | <blue>{module}</blue> | <lvl>{level}</lvl> | "
                                             "{message}", serialize=False)


class Console(Ui):
    def __init__(self, converter: Converter):
        super().__init__()
        self.__converter = converter
        self._menu_options = {
            "0": ("Помощь", self._print_help),
            "1": ("Конвертировать валюту в рубли", self._convert),
            "99": ("Выход", None),
        }

    async def _print_menu(self):
        for key, (description, _) in self._menu_options.items():
            if int(key) < 100:
                print(f"{key} - {description}")

    async def _print_help(self):
        print("""----\nПравила конвертации:
        Введите выражение в формате: '<количество валюты> <валюта>'.
        Количество валюты может быть введено как целым числом, так и дробным (например: 1.5).
        Также поддерживаются простые арифметические операции (+, -, *, /).
        Валюту можно ввести в виде кода (USD, EUR, ...) или названия (доллар США, евро, ...).
        ----
        Примеры:
        '100 USD'
        '1.5 EUR'
        '100*10/4 долларов'""")

    async def _convert(self):
        expression = input("----\nВведите что вы хотите конвертировать: ")
        try:
            curr_rates, amount = await self.__converter.parse_request(expression)
            rub_amts = [amount * curr_rate.rate for curr_rate in curr_rates]
            msg = f"----\n{amount:,.2f} {curr_rates[0].curr.symbol} = {rub_amts[0]:,.2f} ₽".replace(",", " ")
        except ValueError as e:
            msg = f"----\nВозникла ошибка: {e}\nПопробуйте написать выражение по-другому"
        print(f"----\n{msg}")

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__run_async())

    async def __run_async(self):
        while True:
            await self._print_menu()

            choice = input("----\nВведите код команды: ")

            if choice in self._menu_options:
                _, handler = self._menu_options[choice]

                if handler:
                    await handler()
                else:
                    print("Выход...")
                    break
            else:
                print("Неверный ввод. Попробуйте ещё раз...")

            input("Нажмите Enter для продолжения...")
