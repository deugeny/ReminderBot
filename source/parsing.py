from datetime import timedelta, datetime
from typing import List

import pytz
from dateparser import search

from config import MINIMUM_SCHEDULING_PERIOD, DATE_SEARCH_SETTINGS, DATE_SEARCH_LANGUAGES


def find_scheduling_datetime(text: str,
                                 min_scheduling_period: timedelta = MINIMUM_SCHEDULING_PERIOD,
                                 settings: dict = DATE_SEARCH_SETTINGS,
                                 languages: List[str] = DATE_SEARCH_LANGUAGES
                                 ) -> datetime | None:
    found_dates = search.search_dates(text, languages=languages, settings=settings)
    if found_dates is None:
        return None

    now = datetime.utcnow().astimezone(pytz.UTC) + min_scheduling_period
    return max([d for _, d in found_dates if d.astimezone(pytz.UTC) > now], default=None)
