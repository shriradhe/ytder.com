"""Database models and configuration."""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os
from pathlib import Path

# Get project root directory (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'video_downloader.db'}")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class
Base = declarative_base()


# Enums
class AdminRole(enum.Enum):
    """Admin user roles"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"


class NotificationStatus(enum.Enum):
    """Email notification status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Page(Base):
    """Page model for CMS pages (About, Privacy, etc.)"""
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    meta_description = Column(String(300))
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Admin(Base):
    """Admin user model"""
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(SQLEnum(AdminRole), default=AdminRole.ADMIN)
    is_active = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=True)
    language = Column(String(10), default='en')
    theme = Column(String(50), default='default')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)


class HomeSection(Base):
    """Home page feature sections (e.g., High Quality, Lightning Fast, etc.)"""
    __tablename__ = "home_sections"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(100), nullable=False)  # Emoji or icon name
    order = Column(Integer, default=0)  # Display order
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DownloadLog(Base):
    """Log of all download attempts"""
    __tablename__ = "download_logs"

    id = Column(Integer, primary_key=True, index=True)
    video_url = Column(Text, nullable=False)
    video_title = Column(String(500))
    format_id = Column(String(50))
    file_size = Column(Integer)  # in bytes
    client_ip = Column(String(50))
    user_agent = Column(String(500))
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    download_date = Column(Date, default=datetime.utcnow().date)
    created_at = Column(DateTime, default=datetime.utcnow)


class PageView(Base):
    """Track page views and traffic"""
    __tablename__ = "page_views"

    id = Column(Integer, primary_key=True, index=True)
    page_path = Column(String(500), nullable=False)
    client_ip = Column(String(50))
    user_agent = Column(String(500))
    referer = Column(String(500))
    view_date = Column(Date, default=datetime.utcnow().date)
    created_at = Column(DateTime, default=datetime.utcnow)


class Settings(Base):
    """Application settings"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text)
    description = Column(String(500))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailNotification(Base):
    """Email notifications log"""
    __tablename__ = "email_notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_email = Column(String(200), nullable=False)
    subject = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    error_message = Column(Text)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class ApiToken(Base):
    """API tokens for mobile apps"""
    __tablename__ = "api_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(200), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    device_info = Column(Text)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)


class Theme(Base):
    """Custom themes"""
    __tablename__ = "themes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    primary_color = Column(String(50), default='#667eea')
    secondary_color = Column(String(50), default='#764ba2')
    background_color = Column(String(50), default='#f5f7fa')
    text_color = Column(String(50), default='#333333')
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Translation(Base):
    """Multi-language translations"""
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    language_code = Column(String(10), index=True, nullable=False)
    key = Column(String(200), index=True, nullable=False)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Notification(Base):
    """Real-time notifications"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey('admins.id'))
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default='info')  # info, success, warning, error
    is_read = Column(Boolean, default=False)
    link = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


class SeoSettings(Base):
    """SEO settings for frontend"""
    __tablename__ = "seo_settings"

    id = Column(Integer, primary_key=True, index=True)
    page_title = Column(String(200), nullable=False)
    meta_description = Column(Text, nullable=False)
    meta_keywords = Column(String(500))
    og_title = Column(String(200))
    og_description = Column(Text)
    og_image = Column(String(500))
    og_url = Column(String(500))
    twitter_card = Column(String(50), default='summary_large_image')
    twitter_title = Column(String(200))
    twitter_description = Column(Text)
    twitter_image = Column(String(500))
    canonical_url = Column(String(500))
    robots = Column(String(100), default='index, follow')
    is_active = Column(Boolean, default=True)
    updated_by = Column(Integer, ForeignKey('admins.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class News(Base):
    """Latest News items for frontend"""
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    news_date = Column(Date, nullable=False)  # Date for the news item
    order = Column(Integer, default=0)  # Display order
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create tables
def init_db():
    """Initialize database and create tables"""
    Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

