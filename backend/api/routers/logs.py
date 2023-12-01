from datetime import datetime
from datetime import datetime

from fastapi import APIRouter, Depends

import api.globals as g
from api.conf import Config, Credentials
from api.models.db import User
from api.models.doc import AskLogDocument
from api.schemas import LogFilterOptions
from api.users import current_super_user
from utils.logger import get_logger

logger = get_logger(__name__)
config = Config()
credentials = Credentials()

router = APIRouter()


def read_last_n_lines(file_path, n, exclude_key_words=None):
    if exclude_key_words is None:
        exclude_key_words = []
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()[::-1]
    except FileNotFoundError:
        return [f"File not found: {file_path}"]
    last_n_lines = []
    for line in lines:
        if len(last_n_lines) >= n:
            break
        if any([line.find(key_word) != -1 for key_word in exclude_key_words]):
            continue
        last_n_lines.append(line)
    return last_n_lines[::-1]


@router.post("/logs/server", tags=["logs"])
async def get_server_logs(_user: User = Depends(current_super_user), options: LogFilterOptions = LogFilterOptions()):
    lines = read_last_n_lines(
        g.server_log_filename,
        options.max_lines,
        options.exclude_keywords
    )
    return lines


@router.get("/logs/completions", tags=["logs"], response_model=list[AskLogDocument])
async def get_completion_logs(start_time: datetime = None, end_time: datetime = None, max_results: int = 100,
                              _user: User = Depends(current_super_user)):
    criteria = []
    if start_time:
        criteria.append(AskLogDocument.time >= start_time)
    if end_time:
        criteria.append(AskLogDocument.time <= end_time)
    if not criteria:
        logs = await AskLogDocument.find_all().sort(-AskLogDocument.time).limit(max_results).to_list()
    else:
        logs = await AskLogDocument.find(*criteria).sort(-AskLogDocument.time).limit(max_results).to_list()
    return logs
