import json
import os
from typing import Optional, List, Callable, Dict

import requests
import telegram
from pydantic import ValidationError
# noinspection PyPackageRequirements
from telegram import User as TelegramUser

from . import models


def filter_format_result(data: List | Dict, *,
                         filter_result_function: Optional[Callable] = None,
                         format_result_item: Callable = str):
    if not filter_result_function:
        filter_result_function = lambda item: item

    items = data if isinstance(data, list) else data.items()
    return [format_result_item(item) for item in items if filter_result_function(item)]


def assemble_url(*parts: List[str]):
    # noinspection PyUnresolvedReferences
    parts: List[str] = [part.strip("/") for part in parts if part]
    return "/".join(parts)


def request(*, method=str, endpoint: str, base_url: Optional[str], api_version: Optional[str],
            data: List | Dict = None, headers: Dict = None, auth: Optional = None):
    if not base_url:
        base_url = os.getenv("API_BASE_URL", None) or "http://localhost:5000"
    if not api_version:
        api_version = os.getenv("API_VERSION", None) or "v1"
    # noinspection PyTypeChecker
    # none of the input strings can be `None` at this point
    url = assemble_url(base_url, api_version, endpoint)
    if not headers:
        headers = {}

    if data:
        headers['Content-Type'] = "application/json"
        data = json.dumps(data)
    # noinspection PyTypeChecker
    # method being of type `Type[str]` is perfectly fine and seems like an erroneous type error here
    return requests.request(method=method, url=url, data=data, headers=headers, auth=auth)


def get(endpoint: str, *, base_url: Optional[str] = None, api_version: Optional[str] = None, headers: Dict = None,
        auth: Optional = None) -> List | Dict | str:
    # noinspection PyTypeChecker
    # why python thinks `"GET"` is `Type[str]` instead of simply `str` and complains about it is a mistery to me
    response = request(method="GET", endpoint=endpoint, base_url=base_url, api_version=api_version, headers=headers,
                       auth=auth)
    if response.ok:
        return response.json()

    # TODO: error handling
    return f"[{response.status_code}] {response.text}"


def post(endpoint: str, data: Dict, *, base_url: Optional[str] = None, api_version: Optional[str] = None,
         headers: Dict = None, auth: Optional = None) -> List | Dict | str:
    # noinspection PyTypeChecker
    # why python thinks `"POST"` is `Type[str]` instead of simply `str` and complains about it is a mistery to me
    response = request(method="POST", endpoint=endpoint, base_url=base_url, api_version=api_version, headers=headers,
                       auth=auth, data=data)
    if response.ok:
        return response.json()

    # TODO: error handling
    return f"[{response.status_code}] {response.text}"


def patch(endpoint: str, data: Dict, *, base_url: Optional[str] = None, api_version: Optional[str] = None,
          headers: Dict = None, auth: Optional = None) -> List | Dict | str:
    # noinspection PyTypeChecker
    # why python thinks `"POST"` is `Type[str]` instead of simply `str` and complains about it is a mistery to me
    response = request(method="PATCH", endpoint=endpoint, base_url=base_url, api_version=api_version, headers=headers,
                       auth=auth, data=data)
    if response.ok:
        return response.json()

    # TODO: error handling
    return f"[{response.status_code}] {response.text}"


def users():
    format_result_item = lambda d: str(models.User.parse_obj(d))
    endpoint = "/user"
    items = get(endpoint)
    if isinstance(items, str):
        return [items]

    return filter_format_result(items, format_result_item=format_result_item)


def festivals():
    format_result_item = lambda d: str(models.Festival.parse_obj(d))
    endpoint = "/festival"
    items = get(endpoint)
    if isinstance(items, str):
        return [items]

    items = filter_format_result(items, format_result_item=format_result_item)

    return items


def get_attendance(*, festival_id: Optional[int], telegram_id: Optional[int]):
    format_result_item = lambda d: str(models.FestivalAttendee.parse_obj(d))
    filter_condition = lambda item: item

    if telegram_id:
        endpoint = f"/status/{telegram_id}"
    elif festival_id:
        endpoint = f"/festival/{festival_id}/attendees"
    else:
        raise ValueError("either `festival` or `user` needs to be set")

    items = get(endpoint)
    if isinstance(items, str):
        return [items]

    items = filter_format_result(items, format_result_item=format_result_item, filter_result_function=filter_condition)
    return items


def login(user: TelegramUser) -> list | dict | str:
    return post("/user", {
        "telegram_id": user.id,
        "name": user.full_name,
    })


def add_festival(name: str, start: str, end: str, link: Optional[str]):
    result = post("/festival", {
        "name": name,
        "start": start,
        "end": end,
        "link": link,
    })

    try:
        return models.Festival.parse_obj(result)
    except ValidationError:
        return result


def search_festival(festival_query: str):
    format_result_item = lambda d: models.Festival.parse_obj(d)
    endpoint = "/festival/search"
    items = post(endpoint, {
        "name": festival_query
    })
    if isinstance(items, str):
        return [items]

    items = filter_format_result(items, format_result_item=format_result_item)

    return items


def attend(festival: models.Festival, user: telegram.User, status: models.AttendanceStatus):
    endpoint = f"user/{user.id}/attend"
    data = {
        "festival_id": festival.id,
        "status": status.value,
    }
    result = patch(endpoint, data)
    if isinstance(result, str):
        # TODO: fix error handling
        if "[404]" in result:
            return post(endpoint, data)

    return result
