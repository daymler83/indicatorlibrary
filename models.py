from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from sqlalchemy.sql import func



Base = declarative_base()

class Indicator(Base):
    __tablename__ = "indicators"

    id = Column(String, primary_key=True, index=True)
    name = Column(Text)
    definition=Column(Text)
    owner = Column(Text)
    status = Column(Text)
    version = Column(Float)
    dimension = Column(Text)
    sector = Column(Text)
    type=Column(String(20), default='operational')
    priority=Column(String(20), default='medium')
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())

class IndicatorValue(Base):
    __tablename__ = "indicator_values"

    record_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    indicator_id = Column(String, ForeignKey("indicators.id"))
    year = Column(Integer)
    region = Column(Text, nullable=True)
    province = Column(Text, nullable=True)
    gender = Column(Text, nullable=True)
    value = Column(Text, nullable=True)
    unit = Column(Text, nullable=True)
    source = Column(Text, nullable=True)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    tracking_status = Column(Text, nullable=True)
    tracking_message = Column(Text, nullable=True)
    imported_by = Column(String, nullable=True)
    imported_at = Column(DateTime, server_default=func.now())


class IndicatorHistory(Base):
    __tablename__ = "indicator_history"

    history_id = Column(Integer, primary_key=True, autoincrement=True)
    indicator_id = Column(String, index=True)
    name = Column(Text)
    owner = Column(Text)
    status = Column(Text)
    version = Column(Float)
    dimension = Column(Text)
    sector = Column(Text)
    definition = Column(Text)
    changed_at = Column(DateTime, server_default=func.now())
    changed_by = Column(String, nullable=True)  # optional user/email/etc.
    version_number = Column(Integer, default=1)


class ValueHistory(Base):
    __tablename__ = "value_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    indicator_id = Column(String, ForeignKey("indicators.id"))
    year = Column(Integer)
    region = Column(Text, nullable=True)
    province = Column(Text, nullable=True)
    gender = Column(Text, nullable=True)
    value = Column(Text, nullable=True)
    tracking_status = Column(Text, nullable=True)
    tracking_message = Column(Text, nullable=True)
    changed_at = Column(DateTime, server_default=func.now())
    changed_by = Column(String, nullable=True)  # Optional: use user info if available
    imported_by = Column(String, nullable=True)
    imported_at = Column(DateTime, server_default=func.now())
