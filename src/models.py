"""Data models for API requests and responses."""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime, date


# Video Download Models
class VideoRequest(BaseModel):
    """Request model for video URL submission."""
    url: HttpUrl = Field(..., description="Video URL to process")
    format_id: Optional[str] = Field(None, description="Specific format ID (optional)")


class FormatInfo(BaseModel):
    """Information about a single video/audio format."""
    format_id: str = Field(..., description="Format ID for selection")
    ext: str = Field(..., description="File extension")
    quality: str = Field(..., description="Quality description (e.g., '1080p', '720p')")
    format_note: Optional[str] = Field(None, description="Additional format notes")
    filesize: Optional[int] = Field(None, description="File size in bytes")
    filesize_approx: Optional[int] = Field(None, description="Approximate file size in bytes")
    tbr: Optional[float] = Field(None, description="Total bitrate")
    vcodec: Optional[str] = Field(None, description="Video codec")
    acodec: Optional[str] = Field(None, description="Audio codec")
    fps: Optional[float] = Field(None, description="Frames per second")
    resolution: Optional[str] = Field(None, description="Resolution (e.g., '1920x1080')")
    format_type: str = Field(..., description="Type: 'video', 'audio', or 'combined'")


class FormatsResponse(BaseModel):
    """Response model containing available formats."""
    success: bool = Field(..., description="Whether the operation succeeded")
    title: str = Field(..., description="Video title")
    thumbnail: Optional[str] = Field(None, description="Thumbnail URL")
    duration: Optional[float] = Field(None, description="Duration in seconds")
    uploader: Optional[str] = Field(None, description="Video uploader")
    view_count: Optional[int] = Field(None, description="View count")
    formats: List[FormatInfo] = Field(..., description="List of available formats")


class VideoResponse(BaseModel):
    """Response model containing video metadata and download link."""
    success: bool = Field(..., description="Whether the operation succeeded")
    title: str = Field(..., description="Video title")
    url: str = Field(..., description="Direct download URL")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    format: Optional[str] = Field(None, description="Format description")
    duration: Optional[float] = Field(None, description="Duration in seconds")
    thumbnail: Optional[str] = Field(None, description="Thumbnail URL")


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(default=False)
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")


# Admin Models
class AdminLogin(BaseModel):
    """Admin login request."""
    username: str
    password: str


class AdminToken(BaseModel):
    """Admin token response."""
    access_token: str
    token_type: str = "bearer"


class PageCreate(BaseModel):
    """Create page request."""
    slug: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    meta_description: Optional[str] = Field(None, max_length=300)
    is_published: bool = True


class PageUpdate(BaseModel):
    """Update page request."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    meta_description: Optional[str] = Field(None, max_length=300)
    is_published: Optional[bool] = None


class PageResponse(BaseModel):
    """Page response model."""
    id: int
    slug: str
    title: str
    content: str
    meta_description: Optional[str]
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PageListItem(BaseModel):
    """Page list item (without full content)."""
    id: int
    slug: str
    title: str
    meta_description: Optional[str]
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Home Section Models
class HomeSectionCreate(BaseModel):
    """Create home section request."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    icon: str = Field(..., min_length=1, max_length=100)
    order: int = Field(default=0)
    is_active: bool = True


class HomeSectionUpdate(BaseModel):
    """Update home section request."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    icon: Optional[str] = Field(None, min_length=1, max_length=100)
    order: Optional[int] = None
    is_active: Optional[bool] = None


class HomeSectionResponse(BaseModel):
    """Home section response model."""
    id: int
    title: str
    description: str
    icon: str
    order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Statistics Models
class DailyStats(BaseModel):
    """Daily statistics."""
    date: str
    downloads: int
    page_views: int


class MonthlyStats(BaseModel):
    """Monthly statistics."""
    month: str
    downloads: int
    page_views: int


class OverallStats(BaseModel):
    """Overall statistics."""
    total_downloads: int
    total_page_views: int
    today_downloads: int
    today_views: int
    this_month_downloads: int
    this_month_views: int


# Settings Models
class SettingCreate(BaseModel):
    """Create setting request."""
    key: str = Field(..., min_length=1, max_length=100)
    value: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)


class SettingUpdate(BaseModel):
    """Update setting request."""
    value: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)


class SettingResponse(BaseModel):
    """Setting response model."""
    id: int
    key: str
    value: Optional[str]
    description: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True


# Password Change Model
class PasswordChange(BaseModel):
    """Password change request."""
    old_password: str
    new_password: str = Field(..., min_length=6)


# Admin User Management Models
class AdminCreate(BaseModel):
    """Create admin user request."""
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., min_length=5, max_length=200)
    password: str = Field(..., min_length=6)
    role: str = Field(default="admin")


class AdminUpdate(BaseModel):
    """Update admin user request."""
    email: Optional[str] = Field(None, min_length=5, max_length=200)
    role: Optional[str] = None
    is_active: Optional[bool] = None
    email_notifications: Optional[bool] = None
    language: Optional[str] = Field(None, max_length=10)
    theme: Optional[str] = Field(None, max_length=50)


class AdminResponse(BaseModel):
    """Admin user response model."""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    email_notifications: bool
    language: str
    theme: str
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


# Theme Models
class ThemeCreate(BaseModel):
    """Create theme request."""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    primary_color: str = Field(default='#667eea')
    secondary_color: str = Field(default='#764ba2')
    background_color: str = Field(default='#f5f7fa')
    text_color: str = Field(default='#333333')
    is_default: bool = False


class ThemeUpdate(BaseModel):
    """Update theme request."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class ThemeResponse(BaseModel):
    """Theme response model."""
    id: int
    name: str
    display_name: str
    primary_color: str
    secondary_color: str
    background_color: str
    text_color: str
    is_active: bool
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Translation Models
class TranslationCreate(BaseModel):
    """Create translation request."""
    language_code: str = Field(..., min_length=2, max_length=10)
    key: str = Field(..., min_length=1, max_length=200)
    value: str = Field(..., min_length=1)


class TranslationUpdate(BaseModel):
    """Update translation request."""
    value: str = Field(..., min_length=1)


class TranslationResponse(BaseModel):
    """Translation response model."""
    id: int
    language_code: str
    key: str
    value: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Notification Models
class NotificationResponse(BaseModel):
    """Notification response model."""
    id: int
    admin_id: int
    title: str
    message: str
    type: str
    is_read: bool
    link: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Email Notification Models
class EmailNotificationRequest(BaseModel):
    """Email notification request."""
    recipient: str
    subject: str
    message: str
    notification_type: str = "info"


class EmailNotificationResponse(BaseModel):
    """Email notification response."""
    id: int
    recipient_email: str
    subject: str
    status: str
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# API Token Models
class ApiTokenResponse(BaseModel):
    """API token response."""
    id: int
    token: str
    name: str
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    last_used: Optional[datetime]

    class Config:
        from_attributes = True


# Search Filter Models
class SearchFilters(BaseModel):
    """Search and filter parameters."""
    query: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


# SEO Models
class SeoSettingsCreate(BaseModel):
    """Create SEO settings request."""
    page_title: str = Field(..., min_length=1, max_length=200)
    meta_description: str = Field(..., min_length=1, max_length=500)
    meta_keywords: Optional[str] = Field(None, max_length=500)
    og_title: Optional[str] = Field(None, max_length=200)
    og_description: Optional[str] = None
    og_image: Optional[str] = Field(None, max_length=500)
    og_url: Optional[str] = Field(None, max_length=500)
    twitter_card: Optional[str] = Field(default='summary_large_image', max_length=50)
    twitter_title: Optional[str] = Field(None, max_length=200)
    twitter_description: Optional[str] = None
    twitter_image: Optional[str] = Field(None, max_length=500)
    canonical_url: Optional[str] = Field(None, max_length=500)
    robots: Optional[str] = Field(default='index, follow', max_length=100)
    is_active: bool = True


class SeoSettingsUpdate(BaseModel):
    """Update SEO settings request."""
    page_title: Optional[str] = Field(None, min_length=1, max_length=200)
    meta_description: Optional[str] = Field(None, min_length=1, max_length=500)
    meta_keywords: Optional[str] = Field(None, max_length=500)
    og_title: Optional[str] = Field(None, max_length=200)
    og_description: Optional[str] = None
    og_image: Optional[str] = Field(None, max_length=500)
    og_url: Optional[str] = Field(None, max_length=500)
    twitter_card: Optional[str] = Field(None, max_length=50)
    twitter_title: Optional[str] = Field(None, max_length=200)
    twitter_description: Optional[str] = None
    twitter_image: Optional[str] = Field(None, max_length=500)
    canonical_url: Optional[str] = Field(None, max_length=500)
    robots: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class SeoSettingsResponse(BaseModel):
    """SEO settings response model."""
    id: int
    page_title: str
    meta_description: str
    meta_keywords: Optional[str]
    og_title: Optional[str]
    og_description: Optional[str]
    og_image: Optional[str]
    og_url: Optional[str]
    twitter_card: Optional[str]
    twitter_title: Optional[str]
    twitter_description: Optional[str]
    twitter_image: Optional[str]
    canonical_url: Optional[str]
    robots: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# News Models
class NewsCreate(BaseModel):
    """Create news request."""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    news_date: date = Field(..., description="Date for the news item")
    order: int = Field(default=0)
    is_active: bool = True


class NewsUpdate(BaseModel):
    """Update news request."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    news_date: Optional[date] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


class NewsResponse(BaseModel):
    """News response model."""
    id: int
    title: str
    content: str
    news_date: date
    order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True