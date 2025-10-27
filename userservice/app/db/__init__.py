from sqlalchemy import create_engine

from ..core.config import settings

engine = create_engine(str(settings.DATABASE_URL), pool_recycle=3600)

__all__ = ["engine"]
