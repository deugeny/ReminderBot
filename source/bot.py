from telegram import __version__ as TG_VER, BotCommand
from job_store import PTBSQLAlchemyJobStoreV20

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(f"Данный бот не совместим с Вашей версией  PTB {TG_VER}.")