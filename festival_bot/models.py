import enum
from datetime import datetime
from typing import List

from pydantic import BaseModel


class AttendanceStatus(enum.Enum):
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


class FestivalBase(BaseModel):
    name: str
    start: str
    end: str
    link: str | None = None


class FestivalCreate(FestivalBase):
    date_format = "%d.%m"

    pass


class Festival(FestivalBase):
    id: int
    start: datetime
    end: datetime

    date_format = "%d.%m"

    def __str__(self):
        start = self.start.strftime(self.date_format)
        end = self.end.strftime(self.date_format)

        link = f" {self.link}" if self.link else ""
        return f"{self.name} ({start} - {end}){link}"


class UserBase(BaseModel):
    telegram_id: int
    name: str


class UserCreate(UserBase):
    pass


class ApiUser(UserBase):
    pass


class User(UserBase):
    # festivals: List[Festival] = None

    def __str__(self):
        # festival_count = len(self.festivals)
        # festival_str = "festival" if festival_count == 1 else "festivals"
        #
        # return f"{self.name} [{festival_count}{festival_str}]"
        return self.name


class FestivalAttendeeBase(BaseModel):
    festival_id: int
    status: AttendanceStatus = AttendanceStatus.NO


class FestivalAttendeeCreate(FestivalAttendeeBase):
    pass


class FestivalAttendeeUpdate(FestivalAttendeeBase):
    pass


class FestivalAttendee(FestivalAttendeeBase):
    id: int
    user_id: int
    festival: Festival

    def __str__(self):
        return f"{self.festival} ({self.status})"
