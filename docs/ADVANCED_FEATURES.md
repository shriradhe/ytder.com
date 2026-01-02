# 🚀 Advanced Features Guide

Welcome to the comprehensive guide for all advanced features in the Video Downloader application!

---

## 📧 **Email Notifications**

### Features:
- Automatic email notifications for successful downloads
- Admin notifications for important events
- Email delivery status tracking
- Beautiful HTML email templates
- Bulk email sending capabilities

### Configuration:
Configure your SMTP settings in environment variables:

```env
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=noreply@videodownloader.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
```

### Gmail Setup:
1. Enable 2-factor authentication in your Google account
2. Go to Security → App Passwords
3. Generate a new app password
4. Use the generated password as `MAIL_PASSWORD`

### API Endpoints:
- `POST /api/admin/email/send` - Send email notification
- `GET /api/admin/email/history` - View email history

---

## 👥 **Multiple Admin Users with Roles**

### Roles:
- **SUPER_ADMIN**: Full system access, can manage other admins
- **ADMIN**: Standard admin access, can manage content
- **MODERATOR**: Limited access, can view and moderate content

### Features:
- Role-based access control
- User management (create, update, delete)
- Last login tracking
- Individual user preferences (language, theme, email notifications)

### API Endpoints:
- `GET /api/admin/admins` - List all admins (Super Admin only)
- `POST /api/admin/admins` - Create new admin (Super Admin only)
- `PUT /api/admin/admins/{id}` - Update admin
- `DELETE /api/admin/admins/{id}` - Delete admin (Super Admin only)

### Default Super Admin:
```
Username: admin
Password: admin123
Role: SUPER_ADMIN
⚠️ **Change the password immediately!**
```

---

## 🌐 **Multi-Language Support (i18n)**

### Supported Languages:
- 🇬🇧 English (en)
- 🇪🇸 Spanish (es)
- 🇫🇷 French (fr)
- 🇩🇪 German (de)
- 🇸🇦 Arabic (ar)
- 🇮🇳 Hindi (hi)
- 🇨🇳 Chinese (zh)
- 🇯🇵 Japanese (ja)
- 🇵🇹 Portuguese (pt)
- 🇷🇺 Russian (ru)

### Features:
- Database-backed translations
- Fallback to English for missing translations
- Easy translation management from admin panel
- Automatic language detection
- Per-user language preferences

### API Endpoints:
- `GET /api/admin/languages` - Get available languages
- `GET /api/admin/translations/{language_code}` - Get all translations for a language
- `POST /api/admin/translations` - Create/update translation
- `GET /api/admin/translations` - List all translations

### Usage Example:
```javascript
// In frontend
const lang = user.language || 'en';
const translations = await fetch(`/api/admin/translations/${lang}`);
```

---

## 🎨 **Theme Customization**

### Default Themes:
1. **Default (Purple)** - Original purple gradient theme
2. **Ocean Blue** - Calming blue theme
3. **Nature Green** - Fresh green theme
4. **Dark Mode** - Eye-friendly dark theme

### Theme Properties:
- Primary Color
- Secondary Color
- Background Color
- Text Color
- Active/Inactive status
- Default theme flag

### API Endpoints:
- `GET /api/admin/themes` - List all themes
- `POST /api/admin/themes` - Create new theme
- `PUT /api/admin/themes/{id}` - Update theme
- `DELETE /api/admin/themes/{id}` - Delete theme

### Creating a Custom Theme:
```json
{
  "name": "custom-red",
  "display_name": "Custom Red",
  "primary_color": "#e53935",
  "secondary_color": "#c62828",
  "background_color": "#fafafa",
  "text_color": "#212121",
  "is_default": false
}
```

---

## 📱 **Mobile App API**

### Features:
- Token-based authentication
- Simplified API responses optimized for mobile
- Device management
- Lightweight endpoints
- Mobile-specific error handling

### Authentication:
1. **Register Device:**
```bash
POST /api/mobile/register
{
  "device_name": "My iPhone",
  "device_info": "iOS 15.0"
}

Response:
{
  "token": "secure-token-here",
  "expires_at": "2026-01-01T00:00:00",
  "message": "Device registered successfully"
}
```

2. **Use Token in Headers:**
```bash
GET /api/mobile/video/formats
Headers:
  X-Api-Token: your-token-here
```

### Mobile API Endpoints:
- `POST /api/mobile/register` - Register device and get token
- `GET /api/mobile/verify-token` - Verify token validity
- `POST /api/mobile/video/formats` - Get video formats
- `GET /api/mobile/video/download` - Get download link
- `GET /api/mobile/stats` - Get basic statistics
- `GET /api/mobile/health` - Health check
- `POST /api/mobile/feedback` - Submit feedback

### Token Management:
- Tokens expire after 365 days
- View all tokens in admin panel
- Revoke tokens anytime
- Track last usage

---

## 🔔 **Real-Time Notifications (WebSocket)**

### Features:
- Live download notifications
- Real-time statistics updates
- System alerts
- Instant updates without page refresh
- Per-admin notification targeting

### WebSocket Connection:
```javascript
const adminId = getCurrentAdminId();
const ws = new WebSocket(`ws://localhost:8000/ws/admin/${adminId}`);

ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  
  if (notification.type === 'notification') {
    showNotification(notification.data);
  } else if (notification.type === 'stats_update') {
    updateStats(notification.data);
  }
};
```

### Notification Types:
- **info** - General information
- **success** - Success messages
- **warning** - Warning alerts
- **error** - Error notifications

### API Endpoints:
- `GET /api/admin/notifications` - Get notifications
- `PUT /api/admin/notifications/{id}/read` - Mark as read
- `POST /api/admin/notifications/mark-all-read` - Mark all as read

---

## 📊 **Export Analytics (CSV/PDF)**

### Features:
- Export comprehensive analytics to CSV
- Generate professional PDF reports
- Include charts and graphs in PDFs
- Custom date ranges
- Multiple export formats

### Exported Data:
- Overall statistics
- Daily activity (last 30 days)
- Monthly trends (last 12 months)
- Download logs
- Page views
- Video titles and URLs

### API Endpoints:
- `GET /api/admin/export/analytics/csv` - Export to CSV
- `GET /api/admin/export/analytics/pdf` - Export to PDF

### PDF Report Features:
- Professional formatting
- Color-coded tables
- Statistics summary
- Detailed breakdowns
- Generated date and time
- Confidential document watermark

### CSV Export Features:
- UTF-8 encoded
- Excel-compatible
- All data included
- Easy to import into analytics tools

---

## 🔍 **Advanced Search & Filtering**

### Features:
- Full-text search
- Date range filtering
- Status filtering
- Pagination support
- Sort by relevance

### Search Parameters:
```json
{
  "query": "search term",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "status": "success",
  "limit": 100,
  "offset": 0
}
```

### API Endpoints:
- `POST /api/admin/search/downloads` - Search downloads
- `POST /api/admin/search/pages` - Search pages

### Search Operators:
- **Query**: Searches in title, URL, content
- **Date Range**: Filter by creation/update date
- **Status**: Filter by success/failure or published/draft
- **Limit**: Maximum results per page (max 1000)
- **Offset**: Pagination offset

### Usage Example:
```javascript
const results = await fetch('/api/admin/search/downloads', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'youtube',
    start_date: '2025-01-01',
    limit: 50,
    offset: 0
  })
});

const { total, results, limit, offset } = await results.json();
```

---

## 🛠️ **Advanced Settings**

### Database Backups:
- **Auto-Backup**: Configure automatic backups with cron schedule
- **Manual Backup**: One-click backup from admin panel
- **Backup History**: View all backups with timestamps and sizes
- **Backup Location**: `backups/` directory

### API Configuration:
All settings can be managed via environment variables or the admin panel.

### Performance Tuning:
- Adjust concurrent download limits
- Configure cache TTL
- Set rate limiting thresholds
- Optimize worker processes

---

## 📈 **Analytics & Reporting**

### Real-Time Statistics:
- Total downloads (all-time)
- Total page views (all-time)
- Today's activity
- This month's activity
- Daily trends
- Monthly trends

### Visualizations:
- Line charts for daily/monthly trends
- Bar charts for comparisons
- Interactive Chart.js graphs
- Real-time updates via WebSocket

### Tracking:
- Every download is logged with:
  - Video URL and title
  - Format ID and file size
  - Client IP and user agent
  - Success/failure status
  - Error messages (if failed)
  - Timestamp

- Every page view is tracked with:
  - Page path
  - Client IP and user agent
  - Referer
  - Timestamp

---

## 🔒 **Security Features**

### Authentication:
- JWT tokens with expiration
- Argon2 password hashing
- Role-based access control
- Token refresh mechanism

### API Security:
- Rate limiting per IP
- Request validation (Pydantic)
- SQL injection protection (SQLAlchemy ORM)
- CORS configuration

### Admin Security:
- Password strength requirements (min 6 characters)
- Password change functionality
- Session management
- Last login tracking

---

## 🚀 **Getting Started**

### 1. Install Dependencies:
```bash
python -m pip install -r requirements.txt
```

### 2. Configure Environment:
Create a `.env` file with your settings (see .env.example)

### 3. Initialize Database:
The database will be automatically initialized on first run.

### 4. Start Server:
```bash
python main.py
```

### 5. Access Admin Panel:
Navigate to: `http://localhost:8000/admin`

Login with:
- Username: `admin`
- Password: `admin123`
- Role: `SUPER_ADMIN`

**⚠️ IMPORTANT: Change the password immediately!**

---

## 📝 **API Documentation**

Full API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🆘 **Troubleshooting**

### Email Not Sending:
1. Check SMTP configuration
2. Verify firewall/port settings
3. For Gmail, ensure App Password is used
4. Check email logs: `GET /api/admin/email/history`

### WebSocket Connection Issues:
1. Check browser console for errors
2. Verify WebSocket URL format
3. Ensure admin ID is correct
4. Check server logs

### Mobile API Token Issues:
1. Verify token in `X-Api-Token` header
2. Check token expiration
3. Regenerate token if needed
4. View token status in admin panel

### Performance Issues:
1. Increase `MAX_CONCURRENT_DOWNLOADS`
2. Adjust cache TTL settings
3. Check database size
4. Monitor server resources

---

## 🎓 **Best Practices**

### For Production:
1. ✅ Change default admin password
2. ✅ Use strong SECRET_KEY
3. ✅ Configure proper SMTP settings
4. ✅ Enable HTTPS
5. ✅ Set up database backups
6. ✅ Configure rate limiting
7. ✅ Monitor logs
8. ✅ Use environment variables for secrets

### For Scaling:
1. Use PostgreSQL instead of SQLite
2. Enable Redis for caching
3. Use a reverse proxy (Nginx)
4. Set up load balancing
5. Enable auto-backups
6. Monitor system metrics

---

## 📞 **Support**

For issues or questions:
- Check the logs: `app.log`
- Review API documentation: `/docs`
- Check database: `video_downloader.db`

---

## 🎉 **Feature Summary**

✅ Email Notifications  
✅ Multiple Admin Users with Roles  
✅ Multi-Language Support (10 languages)  
✅ Theme Customization (4 default themes)  
✅ Mobile App API  
✅ Real-Time WebSocket Notifications  
✅ CSV/PDF Export  
✅ Advanced Search & Filtering  
✅ Database Backup & Restore  
✅ Comprehensive Analytics  
✅ Role-Based Access Control  
✅ API Token Management  
✅ Translation Management  
✅ Theme Management  

---

**All features are production-ready and fully functional!** 🚀

Enjoy your advanced Video Downloader application! 🎊

