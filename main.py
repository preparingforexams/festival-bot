from datetime import datetime
from typing import TypeVar, Type, Optional

import peewee
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes, CommandHandler

from festival_bot import required_env, init_db, User, Festival, FestivalAttendee
from festival_bot.decorator import command

T = TypeVar("T")


def list_message_for_model(model: Type[peewee.Model], delimiter: str = "\n", empty_message: str = "Nothing here",
                           order_by_field: Optional[peewee.Field] = None) -> str:
    results = model.select()
    if order_by_field:
        results = results.order_by(order_by_field)

    msg = delimiter.join(map(str, results))
    if not results:
        msg = empty_message

    return msg


@command
async def users(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    msg = list_message_for_model(User)

    await update.message.reply_text(msg)


@command
async def festivals(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    msg = list_message_for_model(Festival, order_by_field=Festival.start)

    await update.message.reply_text(msg, disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN_V2)


@command
async def login(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_user = update.effective_user
    user, new = User.get_or_create(telegram_id=telegram_user.id, name=telegram_user.full_name)

    if new:
        msg = f"Successfully logged into festival bot {telegram_user.full_name}"
        user.save()
    else:
        msg = "You've already been logged in"
    await update.message.reply_text(msg)


@command
async def attend(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_user = update.effective_user
    festival_query = " ".join([arg.strip() for arg in update.effective_message.text.split(" ")[1:]])
    if not festival_query:
        msg = "festival name has to be passed as an argument (/attend {festival name})"
    else:
        try:
            # `**` is ILIKE (https://docs.peewee-orm.com/en/latest/peewee/query_operators.html#query-operators)
            festival = Festival.get(Festival.name ** festival_query)
            attendee, new = FestivalAttendee.get_or_create(festival_id=festival.get_id(), telegram_id=telegram_user.id)

            if new:
                attendee.save()
                msg = f"You're now attending {festival}"
            else:
                msg = f"You're already attending {festival}"

        except peewee.DoesNotExist:
            msg = f"{festival_query} was not found in festivals (execute `/festivals` to list available festivals)"

    await update.message.reply_text(msg, disable_web_page_preview=True)


@command
async def attendance(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_user = update.effective_user
    _attendance = FestivalAttendee.get_for_user(telegram_user.id)

    _festivals = "\n".join([_attendence.festival.name for _attendence in _attendance])
    if _festivals:
        msg = f"You're attending the following festivals:\n{_festivals}"
    else:
        msg = "You're not attending any festivals yet"

    await update.message.reply_text(msg)


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
        festival, new = Festival.get_or_create(name=name, start=start, end=end, link=link)

        if new:
            festival.save()
            msg = f"{festival} has been added"
        else:
            msg = f"{festival} already exists"

    await update.message.reply_text(msg, disable_web_page_preview=True)


def main(token: str) -> None:
    init_db()
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("login", login))
    application.add_handler(CommandHandler("users", users))
    application.add_handler(CommandHandler("festivals", festivals))
    application.add_handler(CommandHandler("add", add_festival))
    application.add_handler(CommandHandler("attend", attend))
    application.add_handler(CommandHandler("attendance", attendance))

    application.run_polling()


if __name__ == "__main__":
    _token = required_env("TELEGRAM_BOT_TOKEN")

    main(_token)
