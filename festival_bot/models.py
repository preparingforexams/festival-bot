from typing import List

import peewee
from peewee import DateTimeField, ForeignKeyField, IntegerField, TextField

from festival_bot.utils import required_env

db = peewee.SqliteDatabase(required_env("SQLITE_PATH"))


def init_db():
    db.connect()
    db.create_tables([Festival, User, FestivalAttendee])


class Festival(peewee.Model):
    name = TextField(unique=True)
    start = DateTimeField()
    end = DateTimeField()
    link = TextField(unique=True, null=True)

    date_format = "%d.%m"

    class Meta:
        database = db

    def __str__(self):
        # these fields have `strftime` methods
        # noinspection PyUnresolvedReferences
        start = self.start.strftime(self.date_format)
        # noinspection PyUnresolvedReferences
        end = self.end.strftime(self.date_format)

        link = self.link
        if link:
            name = f"[{self.name}]({link})"
        else:
            name = self.name

        return f"{name} ({start} - {end})"


class User(peewee.Model):
    telegram_id = IntegerField(unique=True, primary_key=True)
    name = TextField()

    class Meta:
        database = db

    def __str__(self):
        return f"{self.name}"


class FestivalAttendee(peewee.Model):
    festival = ForeignKeyField(Festival, to_field="id")
    telegram = ForeignKeyField(User, to_field="telegram_id")

    class Meta:
        database = db

    @classmethod
    def get_for_festival(cls, festival_id: int) -> List["FestivalAttendee"]:
        return FestivalAttendee.select().where(FestivalAttendee.festival == festival_id)

    @classmethod
    def get_for_user(cls, telegram_id: int) -> List["FestivalAttendee"]:
        query = FestivalAttendee.select().where(FestivalAttendee.telegram == telegram_id)
        return query.execute()
