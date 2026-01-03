# Proxy and Cookies Configuration

This document explains how to configure proxies (for geo-blocking bypass) and cookies (for authentication) in the video downloader service.

## Overview

The service now supports:
- **Proxies**: Route all requests through a proxy server to bypass geo-blocking restrictions
- **Cookies**: Automatically use cookies from a file for all requests (enables access to age-restricted content, private videos, etc.)

Both features are configured via environment variables and are automatically applied to all video download requests.

## Proxy Configuration

### Supported Proxy Types

The service supports the following proxy protocols:
- **HTTP**: `http://host:port`
- **HTTPS**: `https://host:port`
- **SOCKS4**: `socks4://host:port`
- **SOCKS5**: `socks5://host:port`

### Configuration

Set the `PROXY` environment variable with your proxy URL:

```bash
# HTTP/HTTPS proxy
export PROXY="http://proxy.example.com:8080"

# SOCKS5 proxy
export PROXY="socks5://proxy.example.com:1080"

# Proxy with authentication
export PROXY="http://username:password@proxy.example.com:8080"
```

### For Render.com Deployment

1. Go to your Render service dashboard
2. Navigate to **Environment** tab
3. Add a new environment variable:
   - **Key**: `PROXY`
   - **Value**: Your proxy URL (e.g., `socks5://proxy.example.com:1080`)
4. Save and redeploy

### Use Cases

- **Geo-blocking bypass**: Access content restricted to specific regions
- **Privacy**: Route traffic through a proxy server
- **Network routing**: Use proxy for network infrastructure requirements

## Cookies Configuration

### Cookie File Format

The service supports cookies in Netscape format (`.txt` files). This is the standard format used by browsers and yt-dlp.

### Exporting Cookies from Browser

#### Chrome/Edge:
1. Install the [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) extension
2. Navigate to the website (e.g., youtube.com)
3. Click the extension icon
4. Click "Export" to download `cookies.txt`

#### Firefox:
1. Install the [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) extension
2. Navigate to the website
3. Click the extension icon
4. Click "Export" to download `cookies.txt`

#### Manual Export (yt-dlp):
```bash
yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://youtube.com"
```

### Configuration

Set the `COOKIES_FILE` environment variable (or `YOUTUBE_COOKIES_FILE` for backwards compatibility) with the path to your cookies file:

```bash
# Local file path
export COOKIES_FILE="/path/to/cookies.txt"

# Or use YOUTUBE_COOKIES_FILE (backwards compatible)
export YOUTUBE_COOKIES_FILE="/path/to/cookies.txt"
```

### For Render.com Deployment

1. **Upload cookies file**:
   - Option A: Add cookies file to your repository (not recommended for security)
   - Option B: Upload to a secure file storage service (S3, etc.)
   - Option C: Generate cookies file during build process

2. **Set environment variable**:
   - Go to Render service dashboard → **Environment** tab
   - Add environment variable:
     - **Key**: `COOKIES_FILE`
     - **Value**: Path to cookies file (e.g., `/opt/render/cookies.txt`)

3. **Update build script** (if using external storage):
   ```bash
   # In build.sh or build command
   # Download cookies file from secure storage
   curl -o cookies.txt https://your-secure-storage.com/cookies.txt
   ```

### Use Cases

- **Age-restricted content**: Access videos with age restrictions
- **Private videos**: Access videos marked as private (if you have permission)
- **Premium content**: Access content requiring authentication
- **Reduced bot detection**: Using authenticated cookies reduces bot detection

## Combined Configuration Example

You can use both proxy and cookies together:

```bash
# .env file
PROXY=socks5://proxy.example.com:1080
COOKIES_FILE=/path/to/cookies.txt
```

Or for Render.com:

**Environment Variables**:
- `PROXY`: `socks5://proxy.example.com:1080`
- `COOKIES_FILE`: `/opt/render/cookies.txt`

## Security Considerations

### Cookies

⚠️ **Important Security Notes**:
- Cookies files contain authentication tokens - **keep them secret**
- Never commit cookies files to version control (add to `.gitignore`)
- Use secure storage for cookies files in production
- Rotate cookies regularly if they expire
- Consider using environment variables or secret management services

### Proxies

- Proxy credentials (if used) are visible in environment variables
- Use secure proxy services for sensitive traffic
- Monitor proxy usage and performance

## Troubleshooting

### Proxy Issues

**Error**: `[Errno -5] No address associated with hostname` or DNS errors
- **Most common cause**: Invalid or unreachable proxy server
- **Quick fix**: 
  1. Go to Render dashboard → Environment
  2. Check if `PROXY` variable exists
  3. **If you don't need proxy**: Delete the `PROXY` variable
  4. **If you need proxy**: Verify the proxy URL is correct and accessible
  5. Redeploy the service
- Verify proxy URL format is correct (must include protocol):
  - ✅ `http://proxy.example.com:8080`
  - ✅ `socks5://proxy.example.com:1080`
  - ❌ `proxy.example.com:8080` (missing protocol - will cause DNS errors)
  - ❌ `http://invalid-host-that-doesnt-exist.com:8080` (unreachable host)

**Error**: Connection timeout
- Check proxy URL is correct
- Verify proxy server is accessible
- Test proxy connectivity: `curl -x $PROXY https://www.google.com`

**Error**: Authentication failed
- Verify proxy credentials are correct
- Check URL format includes credentials: `http://user:pass@host:port`

### Cookies Issues

**Warning**: Cookies file specified but not found
- Verify the file path is correct
- Check file permissions (should be readable)
- Ensure file exists before service starts

**Error**: Invalid cookie format
- Ensure cookies file is in Netscape format
- Verify file encoding is UTF-8
- Check file is not corrupted

### Verification

Check logs on startup to verify configuration:
```
INFO: YtDlpWrapper initialized with max 10 concurrent processes
INFO: Proxy enabled: socks5://proxy.example.com:1080
INFO: Cookies enabled: /path/to/cookies.txt
```

## Testing

To test proxy and cookies configuration:

1. **Test with proxy only**:
   ```bash
   export PROXY="http://proxy.example.com:8080"
   # Make a request to geo-blocked content
   ```

2. **Test with cookies only**:
   ```bash
   export COOKIES_FILE="/path/to/cookies.txt"
   # Make a request to age-restricted content
   ```

3. **Test with both**:
   ```bash
   export PROXY="socks5://proxy.example.com:1080"
   export COOKIES_FILE="/path/to/cookies.txt"
   # Make a request to geo-blocked, age-restricted content
   ```

## Notes

- Cookies and proxy are applied to **all requests** automatically
- Configuration is loaded at startup - restart service after changing environment variables
- Both features work together seamlessly
- No code changes needed - just configure environment variables

