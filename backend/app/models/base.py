import uuid
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    pass


def gen_uuid():
    return str(uuid.uuid4())
