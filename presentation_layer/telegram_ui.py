import os

from business_layer.converter import Converter
from business_layer.scheduler import Scheduler
from models.converted_query import ConvertedQuery
from presentation_layer.presentation import Ui
from functools import wraps
from uuid import uuid4
from datetime import datetime, timedelta
from telegram import (Update, InlineQueryResultArticle, InputTextMessageContent,
                      InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Application, CommandHandler, ContextTypes, InlineQueryHandler, CallbackQueryHandler,
                          PicklePersistence, MessageHandler, filters)
import sys
from loguru import logger


logger.remove()
logger.add(sys.stdout, level="TRACE", format="<green>{time}</green> | <blue>{module}</blue> | <lvl>{level}</lvl> | "
                                             "{message}", serialize=False)
PERSISTENCE_FILE = os.getenv("PERSISTENCE_FILE")


class TelegramBot(Ui):
    def __init__(self, converter: Converter, token: str, botname: str, subscriber: Scheduler = None):
        super().__init__()
        self.app = None
        self.__converter = converter
        if not token:
            raise ValueError("Telegram token is not specified")
        self.__token = token
        if not botname:
            raise ValueError("Telegram botname is not specified")
        self.__botname = botname

        self.help_msg = f"""Бот предназначен для работы в inline-режиме.
        Для его использования в любом чате необходимо ввести выражение в формате: 
        '{self.__botname} <количество валюты> <валюта>'
        
        Количество валюты может быть введено как целым числом, так и дробным (например: 1.5).
        Также поддерживаются простые арифметические операции (+, -, *, /).
        Валюту можно ввести в виде кода (USD, EUR, ...) или названия (доллар США, евро, ...).
        ----
        Примеры:
        '100 USD'
        '1.5 EUR'
        '100*10/4 долларов'"""
        self.subscriber = subscriber
        self.callback_cmds = {}
        if self.subscriber:
            self.callback_cmds.update(self.subscriber.cmds)

    @wraps
    async def reduce_freq(self, func):
        def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if context.user_data.get("last_call", datetime.now() - timedelta(days=1)) > datetime.now() - timedelta(seconds=2):
                logger.warning(f"Too many calls from {update.effective_user.username}")
                return
            context.user_data["last_call"] = datetime.now()
            return func(update, context)
        return wrapper

    async def populate_callback_cmds(self, cmd: str, func: callable):
        self.callback_cmds[cmd] = func

    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        cb_data = update.callback_query.data
        logger.trace(f"{cb_data=}")
        if cb_data["cmd"] not in self.callback_cmds:
            logger.error(f"No callable for {cb_data['cmd']=}")
            return
        res = await self.callback_cmds[update.callback_query.data["cmd"]](update, context)
        if res:
            msg = cb_data["answer"] + "\n\nКоманда успешно выполнена"
        else:
            logger.error(f"Failed to execute {cb_data['cmd']=}")
            return
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=msg, reply_markup=None)
        context.drop_callback_data(update.callback_query)

    @staticmethod
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Бот для перевода из валюты в рубли согласно актуальному курсе ЦБ РФ')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.help_msg)

    async def convert_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.message.text
        if not query:
            return
        logger.trace(f"{query=}")
        try:
            conv_queries = await self.__converter.parse_request(query)
        except ValueError as e:
            logger.error(f"Caught error: {e}")
            await update.message.reply_text("""Неверное выражение, попробуйте написать по-другому.
            Примеры доступны в подсказке /help""")
            return
        logger.trace(f"{conv_queries=}")
        conv_query = conv_queries[0]
        msg = self.converted_query_to_msg(conv_query)
        if self.subscriber:
            reply_markup = self.subscriber.create_inline_keyboard_sub(data_for_scheduler=conv_query.query, answer=msg,
                                                           chat_id=update.message.chat_id)
        else:
            reply_markup = None
        await update.message.reply_text(text=msg, reply_markup=reply_markup)

    @staticmethod
    def converted_query_to_msg(conv_query: ConvertedQuery) -> str:
        logger.trace(f"{conv_query=}")
        sum_rub = f"{conv_query.converted_amount:,.2f}".replace(",", " ")
        logger.trace(f"{sum_rub=}")
        sum_orig = f"{conv_query.original_amount:,.2f}".replace(",", " ")
        logger.trace(f"{sum_orig=}")
        return f"{sum_orig} {conv_query.curr_rate.curr.symbol} = {sum_rub}₽ по курсу ЦБ РФ на сегодня"

    @staticmethod
    def converted_query_to_desc(conv_query: ConvertedQuery) -> str:
        sum_orig = f"{conv_query.original_amount:,.2f}".replace(",", " ")
        return f"Перевести {sum_orig} {conv_query.curr_rate.curr.symbol} в рубли"

    @reduce_freq
    async def inline_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.inline_query.query
        if not query:
            return
        results = []
        logger.trace(f"{query=}")
        try:
            conv_queries = await self.__converter.parse_request(query)
        except ValueError as e:
            logger.error(f"Caught error: {e}")
            return
        logger.trace(f"{conv_queries=}")
        for conv_query in conv_queries:
            msg = self.converted_query_to_msg(conv_query)
            if self.subscriber:
                reply_markup = self.subscriber.create_inline_keyboard_sub(data_for_scheduler=conv_query.query, answer=msg,
                                                               chat_id=update.inline_query.from_user.id)
            else:
                reply_markup = None
            results.append(InlineQueryResultArticle(
                id=str(uuid4()),
                title=conv_query.curr_rate.curr.name,
                description=self.converted_query_to_desc(conv_query),
                input_message_content=InputTextMessageContent(msg),
                reply_markup=reply_markup,
            ))
        await update.inline_query.answer(results)

    async def notify(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = context.job.data
        logger.trace(f"notify: {query=}")
        logger.trace(f"{context.job.chat_id}")
        try:
            conv_queries = await self.__converter.parse_request(query)
        except ValueError as e:
            logger.error(f"Caught error: {e}")
            return
        logger.trace(f"{conv_queries=}")
        conv_query = conv_queries[0]
        reply_markup = self.subscriber.create_inline_keyboard_unsub(query=conv_query.query, chat_id=context.job.chat_id,
                                                                    answer=self.converted_query_to_msg(conv_query))
        await context.bot.send_message(chat_id=context.job.chat_id,
                                       text=self.converted_query_to_msg(conv_query),
                                       reply_markup=reply_markup)

    def run(self):
        logger.info('Starting bot')
        persistence = PicklePersistence(filepath=PERSISTENCE_FILE)
        self.app = (Application.builder()
               .token(self.__token)
               .persistence(persistence)
               .arbitrary_callback_data(True)
               .build())

        if self.subscriber:
            self.subscriber.adjust_tg(self.app, self.notify)
            self.subscriber.set_callback(self.notify)

        # Commands
        self.app.add_handler(CommandHandler('start', self.start_command))
        self.app.add_handler(CommandHandler('help', self.help_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.convert_handler))
        self.app.add_handler(CallbackQueryHandler(self.callback_query_handler))

        # InlineQuery
        self.app.add_handler(InlineQueryHandler(self.inline_query_handler))

        # Errors
        # app.add_error_handler(error)

        logger.info('Start polling')
        self.app.run_polling(poll_interval=2, allowed_updates=Update.ALL_TYPES)