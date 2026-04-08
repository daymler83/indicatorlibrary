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

    texts = relationship("IndicatorText", back_populates="indicator")

class IndicatorText(Base):
    __tablename__ = "indicator_texts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    indicator_id = Column(String, ForeignKey("indicators.id"), index=True)

    language = Column(String(2))  # 'en' | 'ar'

    name = Column(Text)
    definition = Column(Text)
    formula = Column(Text, nullable=True)
    owner = Column(Text)
    dimension = Column(Text)
    sector = Column(Text)

    is_auto_translated = Column(Integer, default=0)
    translation_status = Column(String(20), default='official')
    source_language = Column(String(2))  # 'en' or 'ar'

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())

    indicator = relationship("Indicator", back_populates="texts")


class TranslationCache(Base):
    __tablename__ = "translation_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(128), unique=True, index=True, nullable=False)
    translation_type = Column(String(20), nullable=False, default="text")
    target_lang = Column(String(8), nullable=False)
    source_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    source_model = Column(String(64), nullable=True)
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

class IndicatorTextHistory(Base):
    __tablename__ = "indicator_text_history"

    id = Column(Integer, primary_key=True)
    indicator_id = Column(String)
    language = Column(String(2))
    name = Column(Text)
    definition = Column(Text)
    owner = Column(Text)
    dimension = Column(Text)
    sector = Column(Text)
    changed_at = Column(DateTime, server_default=func.now())
    changed_by = Column(String)
    version_number = Column(Integer)



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


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    data_context = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())

    views = relationship(
        "DepartmentView",
        back_populates="department",
        cascade="all, delete-orphan"
    )
    policy = relationship(
        "DepartmentPolicy",
        back_populates="department",
        uselist=False,
        cascade="all, delete-orphan"
    )


class DepartmentView(Base):
    __tablename__ = "department_views"

    id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey("departments.id"), index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    request_text = Column(Text, nullable=False)
    query_spec = Column(Text, nullable=False)
    query_status = Column(String(20), default="draft")
    last_result_count = Column(Integer, default=0)
    last_refreshed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())

    department = relationship("Department", back_populates="views")


class DepartmentPolicy(Base):
    __tablename__ = "department_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey("departments.id"), unique=True, nullable=False, index=True)
    max_views = Column(Integer, default=10)
    max_indicators_per_view = Column(Integer, default=3)
    max_group_by_fields = Column(Integer, default=2)
    max_filters_per_view = Column(Integer, default=4)
    max_rows = Column(Integer, default=500)
    allowed_view_types = Column(Text, nullable=False, default='["trend","comparison","summary","coverage"]')
    allowed_filters = Column(Text, nullable=False, default='["year_from","year_to","region","province","gender","tracking_status","status","type","priority","sector","dimension"]')
    allowed_dimensions = Column(Text, nullable=False, default='["year","region","province","gender","sector","dimension"]')
    allowed_output_columns = Column(Text, nullable=False, default='["indicator_id","indicator_name","year","region","province","gender","value","unit","tracking_status","tracking_message","status","type","priority","dimension","sector","owner","source","record_count","average_value"]')
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())

    department = relationship("Department", back_populates="policy")

DEFAULT_PERMISSIONS = [
    {"name": "view_indicators", "description": "Can view indicators"},
    {"name": "edit_indicators", "description": "Can create and edit indicators"},
    {"name": "upload_values", "description": "Can upload indicator values"},
    {"name": "approve_indicators", "description": "Can approve indicators"},
    {"name": "manage_users", "description": "Can manage users and permissions"},
    {"name": "view_dashboard", "description": "Can access dashboard features"},
    {"name": "manage_departments", "description": "Can manage departments and AI views"},
    {"name": "export_department_views", "description": "Can export department views to Excel"},
]
