from typing import TypeVar

import telegram
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler

from festival_bot import required_env, commands
from festival_bot.decorator import command
from festival_bot.models import AttendanceStatus

T = TypeVar("T")


@command
async def users(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    _users = commands.users()
    msg = "\n".join(_users)

    await update.message.reply_text(msg, disable_notification=True)


@command
async def festivals(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    _festivals = commands.festivals()
    msg = "\n".join(_festivals)

    await update.message.reply_text(msg, disable_web_page_preview=True, disable_notification=True)


def attend_wrapper(user: telegram.User, message_text: str, status: AttendanceStatus) -> str:
    festival_query = " ".join([arg.strip() for arg in message_text.split(" ")[1:]])
    if not festival_query:
        msg = "festival name has to be passed as an argument"
    else:
        results = commands.search_festival(festival_query)
        if len(results) == 1:
            festival = results[0]
        else:
            msg = "multiple festivals have been found for your search, please be more specific:\n"
            return msg + "\n".join([f.name for f in results])

        _result = commands.attend(festival, user, status)
        if isinstance(_result, str):
            msg = f"failed to update status for festival: {_result}"
        else:
            msg = f"Attendance status for {festival} is now {status}"

    return msg


# noinspection DuplicatedCode
@command
async def attend(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    msg = attend_wrapper(update.effective_user, update.effective_message.text, AttendanceStatus.YES)
    await update.message.reply_text(msg, disable_web_page_preview=True, disable_notification=True)


# noinspection DuplicatedCode
@command
async def attend_no(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    msg = attend_wrapper(update.effective_user, update.effective_message.text, AttendanceStatus.NO)
    await update.message.reply_text(msg, disable_web_page_preview=True, disable_notification=True)


# noinspection DuplicatedCode
@command
async def attend_maybe(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    msg = attend_wrapper(update.effective_user, update.effective_message.text, AttendanceStatus.MAYBE)
    await update.message.reply_text(msg, disable_web_page_preview=True, disable_notification=True)


# noinspection DuplicatedCode
@command
async def attend_ticket(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    msg = attend_wrapper(update.effective_user, update.effective_message.text, AttendanceStatus.HAS_TICKET)
    await update.message.reply_text(msg, disable_web_page_preview=True, disable_notification=True)


@command
async def attendance(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_user = update.effective_user
    _attendance = commands.get_attendance(festival_id=None, telegram_id=telegram_user.id)

    msg = "\n".join(_attendance)
    if not msg:
        msg = "you're not attending any festivals"
    await update.message.reply_text(msg, disable_notification=True, disable_web_page_preview=True)


@command
async def add_festival(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    args = [arg.strip() for arg in update.effective_message.text.split("\n")[1:]]
    if len(args) < 3 or len(args) > 4:
        msg = """/add takes 3 or 4 arguments on separate lines:
{festival name}
{start date (day.month)}
{end date (day.month)}
[{link}]"""
    else:
        name = args[0]
        start = args[1].rstrip(".")
        end = args[2].rstrip(".")
        if len(args) > 3:
            link = args[3].strip()
        else:
            link = None

        # TODO: handle update
        #       -> `peewee.IntegrityError` is thrown when festival any parameter is different than on first insertion
        #       -> maybe an update command? (`/update {festival_name} {key} {value}`)
        festival = commands.add_festival(name=name, start=start, end=end, link=link)

        if isinstance(festival, str):
            msg = f"failed to add festival: {festival}"
        else:
            msg = str(festival)

    await update.message.reply_text(msg, disable_web_page_preview=True, disable_notification=True)


def main(token: str) -> None:
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("users", users))
    application.add_handler(CommandHandler("festivals", festivals))
    application.add_handler(CommandHandler("add", add_festival))
    application.add_handler(CommandHandler("attend", attend))
    application.add_handler(CommandHandler("unattend", attend_no))
    application.add_handler(CommandHandler("maybe", attend_maybe))
    application.add_handler(CommandHandler("ticket", attend_ticket))
    application.add_handler(CommandHandler("attendance", attendance))

    application.run_polling()


if __name__ == "__main__":
    _token = required_env("TELEGRAM_BOT_TOKEN")

    main(_token)
