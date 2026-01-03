# YouTube Extraction Issues

## Common Issue: "Failed to extract any player response"

If you're seeing the error "Failed to extract any player response" when trying to download YouTube videos, this indicates that yt-dlp cannot extract video information from YouTube's API.

## Possible Causes

1. **YouTube IP Blocking**: YouTube may be blocking requests from certain IP address ranges (e.g., cloud hosting providers like Render.com)
2. **Video Restrictions**: The video may have geographic restrictions, age restrictions, or be private
3. **YouTube API Changes**: YouTube frequently changes their API, and yt-dlp needs updates to keep up
4. **Network/Proxy Issues**: Network connectivity or proxy configuration problems

## Solutions

### 1. Use Cookies (Recommended)

Using authenticated cookies can significantly improve success rates by:
- Bypassing bot detection
- Accessing age-restricted content
- Reducing IP-based blocking

**Setup:**
1. Export cookies from your browser (see [PROXY_AND_COOKIES.md](PROXY_AND_COOKIES.md))
2. Set `COOKIES_FILE` environment variable in Render
3. Redeploy service

### 2. Use a Proxy

If YouTube is blocking your server's IP address, use a proxy:

**Setup:**
1. Obtain a proxy server (HTTP, HTTPS, or SOCKS5)
2. Set `PROXY` environment variable in Render
3. Format: `http://proxy-host:port` or `socks5://proxy-host:port`
4. Redeploy service

See [PROXY_AND_COOKIES.md](PROXY_AND_COOKIES.md) for detailed instructions.

### 3. Wait and Retry

Sometimes this is a temporary issue:
- YouTube may have temporary API issues
- Rate limiting may be in effect
- Try again in a few minutes

### 4. Check yt-dlp Version

Ensure you're using the latest yt-dlp version:
- The service automatically upgrades yt-dlp on each deployment
- Check logs for: `yt-dlp version: <version>`
- Current version should be 2025.12.08 or later

### 5. Try Different Videos

Some videos may have specific restrictions:
- Try a different YouTube video to test
- Check if the video is accessible in a browser
- Verify the video isn't private or deleted

## Technical Details

The service tries multiple player clients when extracting YouTube videos:
1. iOS client (`player_client=ios`)
2. Android client (`player_client=android`)
3. Web client (`player_client=web`)
4. Mobile web client (`player_client=mweb`)

If all clients fail, the error is returned to the user.

## Checking Logs

In Render logs, you'll see:
```
INFO - Trying YouTube with player_client=ios
WARNING - Retryable error with player_client=ios: ERROR: [youtube] ...
INFO - Trying YouTube with player_client=android
WARNING - Retryable error with player_client=android: ERROR: [youtube] ...
ERROR - All player clients failed. Last error: ERROR: [youtube] ...
```

This indicates the service tried all available methods before giving up.

## When to Report

Report to yt-dlp GitHub if:
- Issue persists across multiple videos
- All player clients consistently fail
- Issue affects many users
- yt-dlp is on the latest version
- Cookies and proxy are configured correctly

## Related Documentation

- [PROXY_AND_COOKIES.md](PROXY_AND_COOKIES.md) - How to configure proxies and cookies
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - General troubleshooting guide

