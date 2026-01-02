# Video Download Service - Project Summary

## 📋 Project Overview

A high-performance FastAPI-based backend service for video metadata extraction and download link generation. The service supports multiple video platforms (YouTube, Instagram, TikTok, Facebook, Twitter, Vimeo, etc.) and provides a comprehensive admin panel for content management.

**Version:** 1.0.0  
**Framework:** FastAPI (Python 3.9+)  
**Database:** SQLite (configurable to PostgreSQL/MySQL)

---

## 📁 Project Structure

```
ytder_python_backend/
│
├── src/                          # Source code package
│   ├── __init__.py              # Package initialization
│   ├── admin_routes.py          # Admin panel API routes
│   ├── auth.py                  # Authentication & authorization
│   ├── config.py                # Application configuration
│   ├── database.py               # Database models & session management
│   ├── email_service.py         # Email notification service
│   ├── export_service.py        # Data export (CSV/PDF) service
│   ├── mobile_api.py            # Mobile app API endpoints
│   ├── models.py                # Pydantic request/response models
│   ├── service.py               # Core video processing service
│   ├── translation_service.py   # Multi-language translation service
│   ├── websocket_service.py     # WebSocket manager for real-time updates
│   └── ytdlp_wrapper.py         # yt-dlp wrapper for video extraction
│
├── static/                      # Frontend static files
│   ├── index.html               # Main frontend page (with dynamic SEO)
│   ├── admin/                   # Admin panel frontend (AdminLTE 3)
│   │   ├── index.html           # Admin login page
│   │   ├── dashboard.html       # Admin dashboard
│   │   └── dashboard.js         # Dashboard JavaScript
│   └── pages/                   # CMS page viewer
│       └── view.html            # Page viewer template
│
├── docs/                        # Documentation files
│   ├── ADMIN_PANEL_GUIDE.md
│   ├── ADVANCED_FEATURES.md
│   ├── AUTO_FETCH_FEATURE.md
│   ├── BACKUP_TROUBLESHOOTING.md
│   ├── CUSTOM_DOWNLOAD_PROGRESS.md
│   ├── DEVELOPER_GUIDE.md
│   ├── DIRECT_DOWNLOAD_FEATURE.md
│   ├── FORMAT_SELECTION_UPDATE.md
│   ├── INSTANT_DETECTION.md
│   ├── MODERN_UI_DESIGN.md
│   ├── NEW_FEATURES_SUMMARY.md
│   ├── STREAMING_DOWNLOAD_FEATURE.md
│   ├── SUCCESS.md
│   └── WINDOWS_QUICKSTART.md
│
├── data/                        # Data files (databases, backups)
│   ├── video_downloader.db       # Main SQLite database
│   ├── backups/                 # Database backups
│   │   └── backup_*.db
│   └── .gitkeep                 # Keep directory in git
│
├── tests/                       # Test files (to be implemented)
│   └── .gitkeep
│
├── main.py                      # Application entry point (FastAPI app)
├── start.py                     # Quick start script with dependency checks
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup script
├── pyproject.toml               # Modern Python project configuration
├── MANIFEST.in                  # Package manifest
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── LICENSE                      # MIT License
├── README.md                    # Main project documentation
├── PROJECT_SUMMARY.md           # Complete project structure documentation
└── ORGANIZATION_SUMMARY.md      # Organization summary
```

---

## 🏗️ Architecture Overview

### Layer Structure

```
┌─────────────────────────────────────┐
│      FastAPI Application Layer      │
│  (main.py - Routes & Middleware)    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         Service Layer               │
│  (service.py - Caching & Logic)    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      yt-dlp Wrapper Layer           │
│  (ytdlp_wrapper.py - Video Extract)│
└─────────────────────────────────────┘
```

### Key Components

1. **FastAPI Application** (`main.py`)
   - HTTP endpoints for video processing
   - Static file serving
   - WebSocket support
   - CORS middleware
   - Error handling

2. **Service Layer** (`src/service.py`)
   - TTL caching for video metadata
   - Request coalescing (multiple requests share execution)
   - Rate limiting per IP
   - Concurrent request management

3. **Database Layer** (`src/database.py`)
   - SQLAlchemy ORM models
   - Session management
   - Database initialization

4. **Admin Panel** (`src/admin_routes.py`)
   - CMS for pages management
   - User management
   - Analytics & statistics
   - Theme customization
   - Translation management

---

## 📦 Source Code Modules

### Core Modules

| Module | Purpose | Key Features |
|--------|---------|--------------|
| `main.py` | Application entry point | FastAPI app, routes, middleware |
| `service.py` | Video processing service | Caching, rate limiting, request coalescing |
| `ytdlp_wrapper.py` | yt-dlp integration | Async subprocess execution |
| `database.py` | Database models | SQLAlchemy ORM, session management |
| `models.py` | Data models | Pydantic request/response models |
| `config.py` | Configuration | Settings management with pydantic-settings |

### Feature Modules

| Module | Purpose |
|--------|---------|
| `admin_routes.py` | Admin panel API endpoints |
| `auth.py` | JWT authentication, password hashing |
| `mobile_api.py` | Mobile app API endpoints |
| `websocket_service.py` | Real-time WebSocket connections |
| `email_service.py` | Email notification service |
| `export_service.py` | CSV/PDF export functionality |
| `translation_service.py` | Multi-language support |

---

## 🗄️ Database Schema

### Main Tables

- **`admins`** - Admin user accounts with roles
- **`pages`** - CMS pages (About, Privacy, etc.)
- **`home_sections`** - Home page feature sections
- **`download_logs`** - Download attempt logs
- **`page_views`** - Page view tracking
- **`settings`** - Application settings
- **`themes`** - Custom theme configurations
- **`translations`** - Multi-language translations
- **`notifications`** - Real-time notifications
- **`email_notifications`** - Email notification logs
- **`api_tokens`** - API tokens for mobile apps
- **`seo_settings`** - SEO settings for frontend (NEW)

---

## 🔌 API Endpoints

### Public Endpoints

- `GET /` - Frontend homepage
- `GET /api/formats` - Get available video formats
- `GET /api/download` - Download video (streaming)
- `POST /api/video` - Get video metadata
- `GET /api/health` - Health check
- `GET /api/pages` - Get published pages
- `GET /api/home-sections` - Get home sections
- `GET /api/seo` - Get active SEO settings (public)
- `GET /page/{slug}` - Get page by slug
- `GET /pages/{slug}` - View page

### Admin Endpoints (`/api/admin/*`)

- `POST /api/admin/login` - Admin login
- `GET /api/admin/me` - Get current admin
- `GET /api/admin/stats` - Get statistics
- `GET /api/admin/pages` - Manage pages
- `GET /api/admin/downloads` - Download logs
- `GET /api/admin/analytics` - Analytics data
- `GET /api/admin/export` - Export data (CSV/PDF)
- `GET /api/admin/users` - Admin user management
- `GET /api/admin/themes` - Theme management
- `GET /api/admin/translations` - Translation management
- `GET /api/admin/seo` - Get SEO settings
- `POST /api/admin/seo` - Create/update SEO settings
- `GET /api/admin/seo/history` - SEO settings history

### WebSocket

- `WS /ws/admin/{admin_id}` - Real-time notifications

---

## ⚙️ Configuration

Configuration is managed through `src/config.py` and environment variables:

| Setting | Default | Description |
|---------|---------|-------------|
| `HOST` | `127.0.0.1` | Server host |
| `PORT` | `8000` | Server port |
| `MAX_CONCURRENT_DOWNLOADS` | `10` | Max parallel yt-dlp processes |
| `CACHE_TTL_SECONDS` | `3600` | Cache expiration (1 hour) |
| `CACHE_MAX_SIZE` | `1000` | Maximum cached items |
| `RATE_LIMIT_PER_MINUTE` | `30` | Requests per IP per minute |
| `YTDLP_TIMEOUT_SECONDS` | `60` | Max yt-dlp execution time |

Create a `.env` file in the project root to override defaults.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- pip
- yt-dlp (installed via pip or system package)

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify yt-dlp:**
   ```bash
   yt-dlp --version
   ```

3. **Start the server:**
   ```bash
   python start.py
   # OR
   python main.py
   # OR
   uvicorn main:app --host 127.0.0.1 --port 8000
   ```

4. **Access the application:**
   - Frontend: http://localhost:8000
   - Admin Panel: http://localhost:8000/admin
   - API Docs: http://localhost:8000/docs

### Default Admin Credentials

- **Username:** `admin`
- **Password:** `admin123`
- **⚠️ Change immediately in production!**

---

## 📚 Documentation Files

All documentation is located in the `docs/` directory:

- **ADMIN_PANEL_GUIDE.md** - Admin panel usage guide
- **ADVANCED_FEATURES.md** - Advanced features documentation
- **AUTO_FETCH_FEATURE.md** - Auto-fetch feature details
- **CUSTOM_DOWNLOAD_PROGRESS.md** - Download progress tracking
- **DIRECT_DOWNLOAD_FEATURE.md** - Direct download implementation
- **FORMAT_SELECTION_UPDATE.md** - Format selection feature
- **INSTANT_DETECTION.md** - Instant video detection
- **MODERN_UI_DESIGN.md** - UI design documentation
- **NEW_FEATURES_SUMMARY.md** - New features overview
- **STREAMING_DOWNLOAD_FEATURE.md** - Streaming download feature
- **WINDOWS_QUICKSTART.md** - Windows-specific setup guide

---

## 🔧 Development

### Project Organization Principles

1. **Separation of Concerns**
   - Source code in `src/`
   - Documentation in `docs/`
   - Data files in `data/`
   - Tests in `tests/`

2. **Import Structure**
   - Root-level `main.py` imports from `src` package
   - Source modules use relative imports (`.module`)
   - Clean package structure with `__init__.py`

3. **Database Management**
   - Database files stored in `data/` directory
   - Backups in `data/backups/`
   - Path resolution relative to project root

### Adding New Features

1. Add new modules to `src/` directory
2. Use relative imports within `src/`
3. Import from `src` in `main.py`
4. Update this summary document

---

## 🧪 Testing

Test files should be placed in the `tests/` directory. Structure:

```
tests/
├── test_service.py
├── test_api.py
├── test_database.py
└── ...
```

Run tests with:
```bash
pytest tests/
```

---

## 📊 Performance Features

1. **TTL Caching** - Automatic cache expiration
2. **Request Coalescing** - Multiple requests for same URL share execution
3. **Concurrent Processing** - Semaphore-controlled parallel processing
4. **Rate Limiting** - Per-IP request throttling
5. **Async I/O** - Non-blocking subprocess execution

---

## 🔒 Security Features

1. **JWT Authentication** - Secure token-based auth
2. **Password Hashing** - Argon2 password hashing
3. **Role-Based Access** - Admin roles (SUPER_ADMIN, ADMIN, MODERATOR)
4. **Rate Limiting** - DDoS protection
5. **Input Validation** - Pydantic request validation

---

## 📝 License

MIT License - Use freely for personal and commercial projects.

---

## 🤝 Contributing

This is a production-ready template. Customize as needed for your use case.

---

**Last Updated:** December 29, 2025  
**Project Structure Version:** 1.0.0

