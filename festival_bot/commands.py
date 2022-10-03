from datetime import datetime
from typing import Tuple, Optional, Type

import peewee
# noinspection PyPackageRequirements
import telegram

from .models import AttendanceStatus, Festival, FestivalAttendee, User
from .utils import list_message_for_model


def get_or_create(model: Type[peewee.Model], **kwargs):
    return model.get_or_create(**kwargs)


def delete(model: Type[peewee.Model], *expressions) -> int:
    return model.delete().where(*expressions).execute()


def login(user: telegram.User):
    return get_or_create(User, telegram_id=user.id, name=user.full_name)


def users() -> str:
    return list_message_for_model(User)


def festivals() -> str:
    return list_message_for_model(Festival, order_by_field=Festival.start)


def add_festival(name: str, start: datetime, end: datetime, link: Optional[str]) -> Tuple[Festival, bool]:
    return get_or_create(Festival, name=name, start=start, end=end, link=link)


def get_festival(festival_query) -> Festival:
    return Festival.get(Festival.name ** festival_query)


def get_festival_attendee(*, festival: Optional[Festival], user: Optional[telegram.User]):
    if user:
        attendee = FestivalAttendee.get_for_user(user.id)
    elif festival:
        attendee = FestivalAttendee.get_for_festival(festival.get_id())
    else:
        raise ValueError("either `festival` or `user` needs to be set")

    return attendee


def attend(festival: Festival, user: telegram.User, status: AttendanceStatus) -> int | Tuple[FestivalAttendee, bool]:
    match status:
        case AttendanceStatus.NO:
            return delete(FestivalAttendee,
                          FestivalAttendee.festival == festival.get_id(),
                          FestivalAttendee.telegram == user.id)
    return get_or_create(FestivalAttendee, festival_id=festival.get_id(), telegram_id=user.id, status=status.value)
