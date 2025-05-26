from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship



Base = declarative_base()

class Indicator(Base):
    __tablename__ = "indicators"

    id = Column(String, primary_key=True, index=True)
    name = Column(Text)
    definition=Column(Text)
    formula=Column(Text, nullable=True)
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


# Grating permissions

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1)  # use Boolean if preferred
    created_at = Column(DateTime, server_default=func.now())

    permissions = relationship(
    "Permission",
    secondary="user_permissions",
    back_populates="users",
    foreign_keys="[UserPermission.user_id, UserPermission.permission_id]"  # 👈 Fix here
    )



class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    users = relationship(
    "User",
    secondary="user_permissions",
    back_populates="permissions",
    foreign_keys="[UserPermission.user_id, UserPermission.permission_id]"  # 👈 Match
    )


class UserPermission(Base):
    __tablename__ = "user_permissions"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), primary_key=True)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime, server_default=func.now())

DEFAULT_PERMISSIONS = [
    {"name": "view_indicators", "description": "Can view indicators"},
    {"name": "edit_indicators", "description": "Can create and edit indicators"},
    {"name": "upload_values", "description": "Can upload indicator values"},
    {"name": "approve_indicators", "description": "Can approve indicators"},
    {"name": "manage_users", "description": "Can manage users and permissions"},
    {"name": "view_dashboard", "description": "Can access dashboard features"}
]
