# Database Backup Troubleshooting Guide

## Issue: Laravel Route Error When Clicking Backup

If you're seeing a Laravel error (`Route [auth.login] not defined`) when clicking "Backup Database", this indicates you're accessing a **different application** (Laravel/PHP) instead of the Python FastAPI application.

## Solution

### 1. Verify You're Accessing the Correct Application

**Python FastAPI Application:**
- URL should be: `http://localhost:8000` or `http://127.0.0.1:8000`
- Admin panel: `http://localhost:8000/admin`
- API docs: `http://localhost:8000/docs`

**Check if Python app is running:**
```bash
# In the project directory
python main.py
# or
python start.py
```

### 2. Verify the Backup Route

The backup route in the Python FastAPI app is:
- **POST** `/api/admin/database/backup`
- Requires authentication (Bearer token)

### 3. Fixed Issues

The backup functionality has been updated to:
- ✅ Use correct database path from `data/video_downloader.db`
- ✅ Save backups to `data/backups/` directory
- ✅ Handle paths correctly with the new project structure

### 4. Test the Backup Endpoint

You can test the backup endpoint directly:

```bash
# Get your admin token first (login via /api/admin/login)
# Then test backup:
curl -X POST http://localhost:8000/api/admin/database/backup \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json"
```

### 5. Check Browser Console

Open browser developer tools (F12) and check:
1. **Network tab** - See which URL is being called
2. **Console tab** - Check for JavaScript errors
3. Verify the API call goes to: `/api/admin/database/backup`

### 6. Common Issues

#### Issue: Multiple Applications Running
If you have both Laravel and Python apps:
- Make sure they're on different ports
- Python FastAPI: port 8000
- Laravel: typically port 8000 or 8080
- Stop the Laravel app or use a different port

#### Issue: Wrong URL
- Make sure you're accessing `http://localhost:8000` (Python app)
- Not `http://10.150.186.17:8000` (might be Laravel app)

#### Issue: Proxy/Nginx Routing
If using a reverse proxy:
- Check proxy configuration
- Ensure `/api/admin/*` routes go to Python FastAPI
- Not to Laravel application

### 7. Verify Backup Works

After fixing the routing issue, the backup should:
1. Create a file in `data/backups/backup_YYYYMMDD_HHMMSS.db`
2. Return success response with filename and size
3. Show in the backups list in admin panel

### 8. Manual Backup

If the web interface doesn't work, you can manually backup:

```bash
# Windows PowerShell
Copy-Item "data\video_downloader.db" "data\backups\backup_manual_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"

# Linux/Mac
cp data/video_downloader.db "data/backups/backup_manual_$(date +%Y%m%d_%H%M%S).db"
```

## Updated Code

The backup route has been updated in `src/admin_routes.py` to:
- Use `DATA_DIR` from `src/database.py`
- Save to `data/backups/` directory
- Handle database path correctly

## Still Having Issues?

1. Check server logs for errors
2. Verify database file exists at `data/video_downloader.db`
3. Check file permissions for `data/backups/` directory
4. Ensure you're logged in as admin (check token in localStorage)

