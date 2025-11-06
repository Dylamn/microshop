from datetime import datetime

from sqlalchemy import DateTime, func, text
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    A mixin class for handling timestamp information in database models.

    This class is designed to be used as a mixin for database models that need to
    include timestamp fields. It automatically assigns creation and update
    timestamps to the corresponding attributes when records are created or updated
    in the database.

    Attributes:
        created_at (Mapped[datetime]): The timestamp marking the creation of the
            record. It is assigned when the record is first created.
        updated_at (Mapped[datetime]): The timestamp marking the last update of the
            record. It is updated each time the record is modified.
    """
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=text("CURRENT_TIMESTAMP"), nullable=True)
