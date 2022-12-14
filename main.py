from datetime import datetime
from typing import TypeVar

import peewee
import telegram
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler

from festival_bot import required_env, init_db, migrate_db, commands
from festival_bot.decorator import command
from festival_bot.models import AttendanceStatus

T = TypeVar("T")


@command
async def users(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    msg = commands.users()

    await update.message.reply_text(msg, disable_notification=True)


@command
async def festivals(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    msg = commands.festivals()

    await update.message.reply_text(msg, disable_web_page_preview=True, disable_notification=True)


def attend_wrapper(user: telegram.User, message_text: str, status: AttendanceStatus) -> str:
    festival_query = " ".join([arg.strip() for arg in message_text.split(" ")[1:]])
    if not festival_query:
        msg = "festival name has to be passed as an argument"
    else:
        try:
            festival = commands.get_festival(festival_query)
            attendee, new = commands.attend(festival, user, status)

            attendee.save()
            msg = f"Attendance status for {festival} is now {status}"
        except peewee.DoesNotExist:
            msg = f"{festival_query} was not found in festivals (execute `/festivals` to list available festivals)"

    return msg


@command
async def attend(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    msg = attend_wrapper(update.effective_user, update.effective_message.text, AttendanceStatus.YES)
    await update.message.reply_text(msg, disable_web_page_preview=True, disable_notification=True)


@command
async def attend_no(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    msg = attend_wrapper(update.effective_user, update.effective_message.text, AttendanceStatus.NO)
    await update.message.reply_text(msg, disable_web_page_preview=True, disable_notification=True)


@command
async def attend_maybe(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    msg = attend_wrapper(update.effective_user, update.effective_message.text, AttendanceStatus.MAYBE)
    await update.message.reply_text(msg, disable_web_page_preview=True, disable_notification=True)


@command
async def attend_ticket(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    msg = attend_wrapper(update.effective_user, update.effective_message.text, AttendanceStatus.HAS_TICKET)
    await update.message.reply_text(msg, disable_web_page_preview=True, disable_notification=True)


@command
async def attendance(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_user = update.effective_user
    _attendance = commands.get_festival_attendee(festival=None, user=telegram_user)

    _festivals = "\n".join([_attendence.festival.name for _attendence in _attendance])
    if _festivals:
        msg = f"You're attending the following festivals:\n{_festivals}"
    else:
        msg = "You're not attending any festivals yet"

    await update.message.reply_text(msg, disable_notification=True)


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
        start = datetime.strptime(f"{start}.2023", "%d.%m.%Y")
        end = args[2].rstrip(".")
        end = datetime.strptime(f"{end}.2023", "%d.%m.%Y")
        if len(args) > 3:
            link = args[3].strip()
        else:
            link = None

        # TODO: handle update
        #       -> `peewee.IntegrityError` is thrown when festival any parameter is different than on first insertion
        #       -> maybe an update command? (`/update {festival_name} {key} {value}`)
        festival, new = commands.add_festival(name=name, start=start, end=end, link=link)

        if new:
            festival.save()
            msg = f"{festival} has been added"
        else:
            msg = f"{festival} already exists"

    await update.message.reply_text(msg, disable_web_page_preview=True, disable_notification=True)


def main(token: str) -> None:
    init_db()
    migrate_db()
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
