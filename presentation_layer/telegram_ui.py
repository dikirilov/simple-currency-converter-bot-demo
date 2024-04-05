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
HELP_MESSAGE = os.getenv("HELP_MSG")
START_MESSAGE = os.getenv("START_MSG", "Hello!")


class TelegramBot(Ui):
    def __init__(self, converter: Converter, token: str, botname: str, scheduler: Scheduler = None):
        """
        Initialize the Telegram bot with the given converter, token, botname, and optional subscriber.

        Parameters:
            converter (Converter): The converter object to use.
            token (str): The token for the Telegram bot.
            botname (str): The name of the Telegram bot.
            scheduler (Scheduler, optional): The scheduler object if available. Defaults to None.
        """
        super().__init__()
        self.app = None
        self.__converter = converter
        if not token:
            raise ValueError("Telegram token is not specified")
        self.__token = token
        if not botname:
            raise ValueError("Telegram botname is not specified")
        self.__botname = botname

        self.help_msg = HELP_MESSAGE
        self.scheduler = scheduler
        self.callback_cmds = {}
        if self.scheduler:
            self.callback_cmds.update(self.scheduler.cmds)

    @wraps
    async def reduce_freq(self, func):
        """
        A decorator to limit the number of calls to the given function.
        :param update: An update object from PTB
        :param context: A context object from PTB
        """
        def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if context.user_data.get("last_call", datetime.now() - timedelta(days=1)) > datetime.now() - timedelta(seconds=2):
                logger.warning(f"Too many calls from {update.effective_user.username}")
                return
            context.user_data["last_call"] = datetime.now()
            return func(update, context)
        return wrapper

    async def populate_callback_cmds(self, cmd: str, func: callable):
        """
        Populate the callback commands dictionary with the provided command and corresponding function.
        :param cmd: str - the command string
        :param func: callable - the function to associate with the command
        :return: None
        """
        self.callback_cmds[cmd] = func

    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        A function to handle all callback queries. It calls the function associated with the callback query.
        Callback query includes data which should be populated in the button that was clicked.
        The 'cmd' and 'answer' parameters are needed for current handler function, all the others - for corresponding
        function to be called.

        :param update: An update object from PTB
        :param context: A context object from PTB
        """
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
        """
        A function to handle the start command in the Telegram bot. It replies to the user with the START_MESSAGE.

        :param update: An update object from PTB
        :param context: A context object from PTB
        """
        await update.message.reply_text(START_MESSAGE)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            """
            A function to handle the help command in the Telegram bot. It replies to the user with the help message.

            :param update: An update object from PTB
            :param context: A context object from PTB
            """
        await update.message.reply_text(self.help_msg)

    async def convert_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        A function to handle the conversion of a user input query to a response message.
        It processes the queries from chat with bot (not from inline queries), so it chooses the first matched
        currency, but not letting choose.

        :param update: An update object from PTB
        :param context: A context object from PTB
        """
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
        if self.scheduler:
            reply_markup = self.scheduler.create_inline_keyboard_sub(data_for_scheduler=conv_query.query, answer=msg,
                                                                     chat_id=update.message.chat_id)
        else:
            reply_markup = None
        await update.message.reply_text(text=msg, reply_markup=reply_markup)

    @staticmethod
    def converted_query_to_msg(conv_query: ConvertedQuery) -> str:
        """
        A function to compile a message based on ConvertedQuery provided.

        Parameters:
            conv_query (ConvertedQuery): The ConvertedQuery object containing the conversion details.

        Returns:
            str: A formatted message displaying the original and converted amounts with currency symbols.
        """
        logger.trace(f"{conv_query=}")
        sum_rub = f"{conv_query.converted_amount:,.2f}".replace(",", " ")
        logger.trace(f"{sum_rub=}")
        sum_orig = f"{conv_query.original_amount:,.2f}".replace(",", " ")
        logger.trace(f"{sum_orig=}")
        return f"{sum_orig} {conv_query.curr_rate.curr.symbol} = {sum_rub}₽ по курсу ЦБ РФ на сегодня"

    @staticmethod
    def converted_query_to_desc(conv_query: ConvertedQuery) -> str:
        """
        A function to compile a description based on ConvertedQuery provided.

        Args:
            conv_query (ConvertedQuery): The converted query object.

        Returns:
            str: The description of the query in Russian language.
        """
        sum_orig = f"{conv_query.original_amount:,.2f}".replace(",", " ")
        return f"Перевести {sum_orig} {conv_query.curr_rate.curr.symbol} в рубли"

    @reduce_freq
    async def inline_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        A function to handle all inline queries from the Telegram bot.
        Utilizes reduce_freq decorator to limit the number of calls to the given function.

        :param update: An update object from PTB
        :param context: A context object from PTB
        """
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
            if self.scheduler:
                reply_markup = self.scheduler.create_inline_keyboard_sub(data_for_scheduler=conv_query.query, answer=msg,
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
        """
        A function to notify users with subscription. It is called by the scheduler.
        Current implementation assumes, it is the only function that could be used from scheduler.

        Parameters:
            context (ContextTypes.DEFAULT_TYPE): The context object containing job data.
        """
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
        reply_markup = self.scheduler.create_inline_keyboard_unsub(query=conv_query.query, chat_id=context.job.chat_id,
                                                                   answer=self.converted_query_to_msg(conv_query))
        await context.bot.send_message(chat_id=context.job.chat_id,
                                       text=self.converted_query_to_msg(conv_query),
                                       reply_markup=reply_markup)

    def run(self):
        """
        A method to run the bot, setting up various handlers for commands, messages, and errors.
        """
        logger.info('Starting bot')
        persistence = PicklePersistence(filepath=PERSISTENCE_FILE)
        self.app = (Application.builder()
               .token(self.__token)
               .persistence(persistence)
               .arbitrary_callback_data(True)
               .build())

        if self.scheduler:
            self.scheduler.adjust_tg(self.app, self.notify)

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