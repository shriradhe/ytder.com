# Windows Quick Start Guide

## ✅ Server is Running!

Your video download service is now live at:
- **Frontend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health

## 🚀 How to Use

### Option 1: Use the Web Interface
1. Open your browser and go to http://localhost:8000
2. Paste a video URL (YouTube, Vimeo, etc.)
3. Click "Get Download Link"
4. Click the download button when it appears!

### Option 2: Use the API Directly

**PowerShell:**
```powershell
$body = @{
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/video" -Method Post -Body $body -ContentType "application/json"
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/video",
    json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
)
print(response.json())
```

## 📝 Common Commands (Windows)

### Install dependencies:
```powershell
python -m pip install -r requirements.txt
```

### Start server:
```powershell
python main.py
```

### Stop server:
Press `Ctrl+C` in the terminal where the server is running

### Kill server if stuck:
```powershell
# Find the process on port 8000
netstat -ano | findstr :8000

# Kill it (replace PID with the number from above)
taskkill /F /PID <PID>
```

## 🔧 Configuration

Create a `.env` file in the project root to customize:

```env
HOST=127.0.0.1
PORT=8000
MAX_CONCURRENT_DOWNLOADS=10
CACHE_TTL_SECONDS=3600
RATE_LIMIT_PER_MINUTE=30
```

## 📊 Check Server Health

Open http://localhost:8000/api/health in your browser to see:
- Cache statistics
- Active processes
- Service status

## 🐛 Troubleshooting

### "Port already in use" error:
```powershell
netstat -ano | findstr :8000
taskkill /F /PID <PID>
```

### "pip not found" error:
Use `python -m pip` instead of `pip`:
```powershell
python -m pip install -r requirements.txt
```

### "yt-dlp not found" error:
```powershell
python -m pip install yt-dlp
```

### Unicode errors in startup script:
Use `python main.py` directly instead of `python start.py`

## 📚 Features

- ✅ Async/non-blocking execution
- ✅ Request coalescing (duplicate URLs share one download)
- ✅ Smart caching (1 hour TTL)
- ✅ Rate limiting (30 req/min per IP)
- ✅ Automatic timeout protection
- ✅ Beautiful web UI
- ✅ OpenAPI docs at /docs

## 🎯 Supported Sites

Supports 1000+ sites via yt-dlp, including:
- YouTube
- Vimeo
- Twitter/X
- TikTok
- Instagram
- Facebook
- And many more!

Full list: https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md

---

**Enjoy your high-performance video download service!** 🎬

