import asyncio
import logging
from logging import INFO

from sqlalchemy import create_engine
from models import Base

from aiogram import Bot, Dispatcher, Router
from dotenv import load_dotenv, dotenv_values

from admin_interface import *
from operator_interface import *

logger = logging.getLogger()
config = dotenv_values()
bot = Bot(config['BOT_TOKEN'], parse_mode="HTML")
dp = Dispatcher(bot=bot)


def __config_logger():
    file_log = logging.FileHandler('telegram-bot.log')
    console_log = logging.StreamHandler()
    FORMAT = '[%(levelname)s] %(asctime)s : %(message)s | %(filename)s'
    logging.basicConfig(level=INFO,
                        format=FORMAT,
                        handlers=(file_log, console_log),
                        datefmt='%d-%m-%y - %H:%M:%S')


async def main():
    dp.include_routers(
        admin_router,
        operator_router
    )
    logger.info('Bot starts')
    await dp.start_polling(bot)


if __name__ == '__main__':
    __config_logger()
    load_dotenv('.env')
    asyncio.run(main())