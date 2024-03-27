from business_layer.converter import Converter
from presentation_layer.presentation import Ui
from uuid import uuid4
from datetime import datetime, timedelta
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, ContextTypes, InlineQueryHandler
import sys
from loguru import logger


logger.remove()
logger.add(sys.stdout, level="TRACE", format="<green>{time}</green> | <blue>{module}</blue> | <lvl>{level}</lvl> | "
                                             "{message}", serialize=False)
#TOKEN = "7181431320:AAGp8NDXTOgerQKT4DjjdMEP-boa45F9rOM"
#BOTNAME = "@Currency2RubConverterBot"


class TelegramBot(Ui):
    def __init__(self, converter: Converter, token: str, botname: str):
        super().__init__()
        self.__converter = converter
        if not token:
            raise ValueError("Telegram token is not specified")
        self.__token = token
        if not botname:
            raise ValueError("Telegram botname is not specified")
        self.__botname = botname

    @staticmethod
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Бот для перевода из валюты в рубли согласно актуальному курсе ЦБ РФ')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"""Бот предназначен для работы в inline-режиме.
        Для его использования в любом чате необходимо ввести выражение в формате: 
        '{self.__botname} <количество валюты> <валюта>'
        
        Количество валюты может быть введено как целым числом, так и дробным (например: 1.5).
        Также поддерживаются простые арифметические операции (+, -, *, /).
        Валюту можно ввести в виде кода (USD, EUR, ...) или названия (доллар США, евро, ...).
        ----
        Примеры:
        '100 USD'
        '1.5 EUR'
        '100*10/4 долларов'""")

    async def inline_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.user_data.get("last_call", datetime.now() - timedelta(days=1)) > datetime.now() - timedelta(seconds=2):
            return
        context.user_data["last_call"] = datetime.now()
        query = update.inline_query.query
        if not query:
            return
        results = []
        try:
            curr_rates, amount = await self.__converter.parse_request(query)
        except ValueError as e:
            logger.error(f"Caught error: {e}")
            return
        logger.trace(f"{amount=}")
        for curr_rate in curr_rates:
            logger.trace(f"{curr_rate=}")
            rub = amount * curr_rate.rate
            sum_orig = f"{amount: ,.2f}".replace(",", " ")
            sum_rub = f"{rub: ,.2f}".replace(",", " ")
            logger.trace(f"{sum_rub=}")
            results.append(InlineQueryResultArticle(
                id=str(uuid4()),
                title=curr_rate.curr.name,
                description=f"Перевести {sum_orig} {curr_rate.curr.symbol} в рубли",
                input_message_content=InputTextMessageContent(
                    f"{sum_orig} {curr_rate.curr.symbol} = {sum_rub}₽ по курсу ЦБ РФ на сегодня"
                ),
            ))
        await update.inline_query.answer(results)

    def run(self):
        logger.info('Starting bot')
        app = Application.builder().token(self.__token).build()

        # Commands
        app.add_handler(CommandHandler('start', self.start_command))
        app.add_handler(CommandHandler('help', self.help_command))

        # InlineQuery
        app.add_handler(InlineQueryHandler(self.inline_query))

        # Errors
        # app.add_error_handler(error)

        logger.info('Start polling')
        app.run_polling(poll_interval=2)