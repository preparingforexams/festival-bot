from typing import Callable, Any

from telegram import Update
from telegram.ext import ContextTypes

from festival_bot import logger
from .commands import login


def command(function: Callable[[Update, ContextTypes], Any]):
    def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        log = logger.create_logger(f"{function.__name__}")
        log.debug("start")

        # `update.effective_user` is always present since this decorator will only be used for telegram commands
        # which need to be executed by a user
        login(update.effective_user)

        try:
            log.debug("execute")
            result = function(update, context)
            log.debug("end")
            return result
        except Exception as e:
            log.error(e)
            log.debug("end")
            raise e

    return wrapper
