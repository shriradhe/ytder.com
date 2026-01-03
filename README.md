# Video Download Service - High-Performance Backend

A production-quality Python backend for video metadata extraction and download link generation using yt-dlp.

## 📁 Project Structure

```
ytder_python_backend/
├── src/              # Source code package (12 modules)
├── static/           # Frontend static files (AdminLTE 3)
├── docs/             # All documentation files (25 files)
├── data/             # Database files and backups
├── tests/            # Test files (ready for implementation)
├── main.py           # Application entry point
├── start.py          # Quick start script
├── requirements.txt  # Python dependencies
├── setup.py          # Package setup
├── pyproject.toml    # Modern Python project config
├── Makefile          # Make commands for common tasks
├── .editorconfig     # Editor configuration
├── .python-version   # Python version
└── LICENSE           # MIT License
```

**📖 For detailed project structure, see:**
- [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) - Complete structure reference
- [docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md) - Project summary

## 🚀 Features

### Performance Optimizations
- **Async/Non-blocking Execution**: FastAPI with full async/await support
- **Concurrent Request Handling**: Semaphore-controlled parallel yt-dlp processes
- **Request Coalescing**: Multiple requests for the same URL share a single yt-dlp execution
- **TTL Caching**: Automatic cache expiration to prevent redundant work
- **Memory Efficient**: Metadata only, no video file storage
- **Rate Limiting**: Per-IP request throttling

### Advanced Features
- **Proxy Support**: Route requests through HTTP/HTTPS/SOCKS proxies for geo-blocking bypass
- **Automatic Cookies**: Use cookies file for all requests (access age-restricted/private content)
- **Apify API Fallback**: Automatic fallback to Apify API when yt-dlp fails (bypasses IP blocking)
- **Multi-platform Support**: YouTube, Instagram, Facebook, TikTok, and 8+ more platforms

### Architecture
```
┌─────────────────┐
│  FastAPI Layer  │  - Request validation, routing, error handling
└────────┬────────┘
         │
┌────────▼────────┐
│ Service Layer   │  - Caching, request coalescing, rate limiting
└────────┬────────┘
         │
┌────────▼────────┐
│  Worker Layer   │  - Async subprocess management, yt-dlp wrapper
└─────────────────┘
```

## 📦 Installation

### Prerequisites
- Python 3.10+ (3.12.0 recommended)
- pip

### Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Verify yt-dlp installation**:
```bash
yt-dlp --version
```

3. **Optional: Create `.env` file** for custom configuration:
```env
HOST=127.0.0.1
PORT=8000
MAX_CONCURRENT_DOWNLOADS=10
CACHE_TTL_SECONDS=3600
RATE_LIMIT_PER_MINUTE=30
YTDLP_TIMEOUT_SECONDS=60

# Proxy for geo-blocking bypass (optional)
PROXY=socks5://proxy.example.com:1080

# Cookies file for authentication (optional)
COOKIES_FILE=/path/to/cookies.txt

# Apify API fallback (optional - when yt-dlp fails)
APIFY_ENABLED=true
APIFY_API_TOKEN=your-apify-token-here
APIFY_ACTOR_ID=apify/youtube-scraper
```

**See [docs/PROXY_AND_COOKIES.md](docs/PROXY_AND_COOKIES.md) for proxy and cookies configuration.**  
**See [docs/APIFY_INTEGRATION.md](docs/APIFY_INTEGRATION.md) for Apify API fallback setup.**

## 🏃 Usage

### Start the server:
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

### Access the frontend:
Open http://localhost:8000 in your browser

### API Endpoints

#### POST `/api/video`
Extract video metadata and download link

**Request**:
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "format_id": null
}
```

**Response**:
```json
{
  "success": true,
  "title": "Rick Astley - Never Gonna Give You Up",
  "url": "https://direct-download-url.com/video.mp4",
  "file_size": 50331648,
  "format": "1080p",
  "duration": 212,
  "thumbnail": "https://thumbnail-url.com/image.jpg"
}
```

#### GET `/api/health`
Health check with service statistics

**Response**:
```json
{
  "status": "healthy",
  "service": "video-download-api",
  "stats": {
    "cache_size": 42,
    "cache_max_size": 1000,
    "in_flight_requests": 3,
    "active_ytdlp_processes": 5
  }
}
```

#### POST `/api/cache/clear`
Clear the cache (admin endpoint)

## ⚙️ Configuration

Edit `src/config.py` or create `.env` file in the project root:

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_CONCURRENT_DOWNLOADS` | 10 | Max parallel yt-dlp processes |
| `CACHE_TTL_SECONDS` | 3600 | Cache expiration time |
| `CACHE_MAX_SIZE` | 1000 | Maximum cached items |
| `RATE_LIMIT_PER_MINUTE` | 30 | Requests per IP per minute |
| `YTDLP_TIMEOUT_SECONDS` | 60 | Max yt-dlp execution time |
| `PROXY` | None | Proxy URL (http/https/socks4/socks5) for geo-blocking bypass |
| `COOKIES_FILE` | None | Path to cookies.txt file for authentication |
| `APIFY_ENABLED` | false | Enable Apify API fallback when yt-dlp fails |
| `APIFY_API_TOKEN` | None | Apify API token (get from https://console.apify.com) |
| `APIFY_ACTOR_ID` | None (required) | Apify actor ID (format: username/actor-name, find at https://apify.com/store) |

**📖 For detailed setup:**
- [Proxy & Cookies](docs/PROXY_AND_COOKIES.md) - Proxy and cookies configuration
- [Apify Integration](docs/APIFY_INTEGRATION.md) - Apify API fallback setup

## 🔥 Performance Characteristics

### Concurrency Model
- **Semaphore**: Limits concurrent yt-dlp processes to prevent resource exhaustion
- **Request Coalescing**: 100+ requests for same URL = 1 yt-dlp execution
- **Non-blocking I/O**: Async subprocess execution with asyncio

### Memory Usage
- **Metadata only**: ~1KB per cached video (no video file storage)
- **TTL Cache**: Auto-expires old entries (configurable)
- **Bounded**: Max cache size prevents unbounded growth

### CPU Optimization
- **Process pooling**: Semaphore-controlled concurrency
- **Subprocess isolation**: yt-dlp runs in separate processes
- **Efficient parsing**: JSON-only output from yt-dlp (no video processing)

## 🛡️ Error Handling

- **Rate Limiting**: 429 status code with retry-after
- **Timeouts**: 504 status code for slow yt-dlp executions
- **Invalid URLs**: 422 validation errors
- **Service Errors**: 500 with detailed error messages

## 📊 Monitoring

Use `/api/health` endpoint to monitor:
- Cache hit ratio (via cache_size)
- Active yt-dlp processes
- In-flight request coalescing

## 📚 Documentation

- **Project Structure**: See [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for complete project organization
- **Admin Panel**: See [docs/ADMIN_PANEL_GUIDE.md](docs/ADMIN_PANEL_GUIDE.md)
- **Advanced Features**: See [docs/ADVANCED_FEATURES.md](docs/ADVANCED_FEATURES.md)
- **Proxy & Cookies**: See [docs/PROXY_AND_COOKIES.md](docs/PROXY_AND_COOKIES.md) for geo-blocking and authentication setup
- **Apify Integration**: See [docs/APIFY_INTEGRATION.md](docs/APIFY_INTEGRATION.md) for Apify API fallback when yt-dlp fails
- **Windows Setup**: See [docs/WINDOWS_QUICKSTART.md](docs/WINDOWS_QUICKSTART.md)

## 🔒 Production Considerations

1. **Rate Limiting**: Adjust `RATE_LIMIT_PER_MINUTE` based on your resources
2. **CORS**: Update `allow_origins` in `main.py` for production domains
3. **Authentication**: Add auth to `/api/cache/clear` endpoint
4. **Logging**: Configure log levels and log aggregation
5. **Monitoring**: Integrate with Prometheus/Grafana for metrics
6. **Resource Limits**: Set appropriate OS limits (ulimit, max processes)
7. **Database**: Consider using PostgreSQL/MySQL for production (update `DATABASE_URL` in `src/database.py`)

## 🧪 Testing

```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Test video extraction
curl -X POST http://localhost:8000/api/video \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

---

**Built with**: FastAPI, yt-dlp, Python asyncio
**Optimized for**: High concurrency, low resource usage, production reliability

