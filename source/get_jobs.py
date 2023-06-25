from typing import Tuple, List

from telegram.ext import Job


def get_jobs(user_id:int, jobs:Tuple["Job['APSJob']"]) -> List["Job['APSJob']"]:
    return list(filter(lambda job: (job.user_id == user_id), jobs))
