from sqlalchemy import create_engine

from ..core.config import get_settings

engine = create_engine(get_settings().DATABASE_URL, pool_recycle=3600)

__all__ = ["engine"]
