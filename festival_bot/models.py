import inspect
from enum import Enum
from typing import List

import peewee
import playhouse
from peewee import DateTimeField, ForeignKeyField, IntegerField, TextField
from playhouse.migrate import SqliteMigrator

from festival_bot.logger import create_logger
from festival_bot.utils import required_env

db = peewee.SqliteDatabase(required_env("SQLITE_PATH"))
migrator = SqliteMigrator(db)


def init_db():
    db.connect()
    db.create_tables([Festival, User, FestivalAttendee])


def migrate_db():
    try:
        playhouse.migrate.migrate(
            migrator.add_column(FestivalAttendee.__name__.lower(), FestivalAttendee.status.column_name,
                                FestivalAttendee.status)
        )
    except peewee.OperationalError as e:
        create_logger(inspect.currentframe().f_code.co_name).error(e)
        pass


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

        link = f" {self.link}" if self.link else ""
        return f"{self.name} ({start} - {end}){link}"


class User(peewee.Model):
    telegram_id = IntegerField(unique=True, primary_key=True)
    name = TextField()

    class Meta:
        database = db

    def __str__(self):
        return f"{self.name}"


class AttendanceStatus(Enum):
    NO = 0
    MAYBE = 1
    YES = 2
    HAS_TICKET = 3

    def __str__(self):
        result = "not attending"

        match self:
            case AttendanceStatus.MAYBE:
                result = "maybe"
            case AttendanceStatus.YES:
                result = "attending"
            case AttendanceStatus.HAS_TICKET:
                result = "has ticket"

        return result


class FestivalAttendee(peewee.Model):
    festival = ForeignKeyField(Festival, to_field="id")
    telegram = ForeignKeyField(User, to_field="telegram_id")
    status = IntegerField(default=AttendanceStatus.YES)

    class Meta:
        database = db

    @classmethod
    def get_for_festival(cls, festival_id: int) -> List["FestivalAttendee"]:
        return FestivalAttendee.select().where(FestivalAttendee.festival == festival_id)

    @classmethod
    def get_for_user(cls, telegram_id: int) -> List["FestivalAttendee"]:
        query = FestivalAttendee.select().where(FestivalAttendee.telegram == telegram_id)
        return query.execute()
