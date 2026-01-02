# 🔧 YouTube Bot Detection Fix

## Issue
YouTube was blocking requests with the error:
```
ERROR: [youtube] 9VN6xUjXdo8: Sign in to confirm you're not a bot.
```

## Solution Applied

### 1. Added Browser-Like Headers
- User-Agent: Modern Chrome browser
- Referer: YouTube domain
- Accept headers: Standard browser headers
- DNT, Connection, Upgrade-Insecure-Requests headers

### 2. YouTube Extractor Args
- Changed to use `player_client=android` instead of web client
- Android client is less likely to trigger bot detection
- More reliable for automated access

### 3. Cookie Support (Optional)
- Added support for cookies via `YOUTUBE_COOKIES_FILE` environment variable
- If cookies file exists, yt-dlp will use it for authentication
- This can help bypass bot detection for authenticated requests

## How to Use Cookies (Optional)

If you want to use cookies to improve success rate:

1. **Export cookies from your browser:**
   - Use a browser extension like "Get cookies.txt LOCALLY"
   - Or use yt-dlp's built-in cookie extraction:
     ```bash
     yt-dlp --cookies-from-browser chrome
     ```

2. **Save cookies to a file:**
   - Save as `cookies.txt` in your project root
   - Or set `YOUTUBE_COOKIES_FILE` environment variable to the path

3. **Set environment variable (Render.com):**
   ```
   YOUTUBE_COOKIES_FILE=/path/to/cookies.txt
   ```

## Testing

After deployment, test with:
- YouTube videos
- YouTube Shorts
- YouTube playlists (single video mode)

The bot detection should be significantly reduced.

## Additional Notes

- The Android client approach is more reliable than web client
- Cookies are optional but recommended for better success rate
- If issues persist, consider rotating user agents or using proxy

## Files Modified

- `src/ytdlp_wrapper.py` - Added `_get_youtube_options()` function
- Updated all three yt-dlp command locations to use the new options

