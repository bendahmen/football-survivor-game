# Football Survivor Game - Deployment & Maintenance Guide

## 🚀 Deployment on Render.com (Free Plan)

### Initial Setup

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add admin sync dashboard for data management"
   git push origin main
   ```

2. **Deploy on Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Create a new Web Service
   - Connect your GitHub repository
   - Use the existing `render.yaml` configuration

3. **Set Environment Variables**
   In Render dashboard, add:
   - `FOOTBALL_DATA_API_KEY`: Your API key from [football-data.org](https://www.football-data.org/)
   - The database URL and secret key will be auto-generated

4. **Initial Data Load**
   The build script will automatically sync teams and fixtures on first deployment.

## 📊 Data Management (No Shell Access on Free Plan!)

Since Render's free plan doesn't provide shell access or cron jobs, we've created a web-based admin dashboard for data management.

### Accessing the Sync Dashboard

1. **Login as Admin**
   - Go to: `https://your-app.onrender.com/admin/`
   - Username: `admin`
   - Password: `changeme123` (CHANGE THIS IMMEDIATELY!)

2. **Navigate to Sync Dashboard**
   - Go to: `https://your-app.onrender.com/survivor/admin/sync/`
   - You must be logged in as a staff member

### Dashboard Features

#### 🔄 Quick Sync All (Recommended)
- One-click button to sync everything
- Updates teams, fixtures, and processes results
- Use this for regular updates

#### Individual Sync Options

1. **Sync Teams**
   - Updates all Bundesliga teams
   - Run this at the start of each season

2. **Sync Fixtures**
   - Options:
     - Season year (e.g., 2024)
     - Specific matchday (1-34)
     - Results only mode (updates scores without creating new fixtures)

3. **Process Results**
   - Processes match results
   - Eliminates players who picked losing teams
   - Run after matches are completed

## 🔧 Regular Maintenance Schedule

### Weekly Tasks (During Season)
1. **Before Each Matchday**
   - Sync fixtures for upcoming matchday
   - Verify all matches are loaded

2. **After Matches Complete**
   - Click "Sync Everything" button
   - Or manually:
     - Sync Fixtures (results only)
     - Process Results

### Season Start
1. Sync Teams (in case of new promoted teams)
2. Full fixture sync for new season
3. Create new game pools

## 🐛 Troubleshooting

### Common Issues

1. **No data showing after deployment**
   - Go to the sync dashboard
   - Click "Sync Everything"
   - Check if FOOTBALL_DATA_API_KEY is set in Render environment variables

2. **Rate limit errors**
   - The free API tier allows 10 requests/minute
   - Wait a minute and try again
   - Use specific matchday syncs instead of full season

3. **Can't access admin dashboard**
   - Ensure you're using the correct admin credentials
   - Check that you're accessing `/survivor/admin/sync/` (not just `/admin/`)

4. **Fixtures not updating**
   - Check the API key is valid
   - Try "Results Only" mode if fixtures already exist
   - Check API status at [football-data.org](https://www.football-data.org/)

## 📝 Management Commands (For Local Development)

If running locally, you can use these commands:

```bash
# Sync teams
python manage.py sync_teams

# Sync fixtures for current season
python manage.py sync_fixtures

# Sync specific matchday
python manage.py sync_fixtures --matchday 15

# Process results
python manage.py process_results

# Update everything
python manage.py update_bundesliga

# Full sync
python manage.py update_bundesliga --full
```

## 🔐 Security Notes

1. **Change the default admin password immediately!**
2. Keep your `FOOTBALL_DATA_API_KEY` secret
3. Use environment variables for sensitive data
4. Enable HTTPS in production (Render provides this)

## 📚 API Information

- **Provider**: football-data.org
- **Free Tier Limits**: 10 requests/minute
- **Competition**: Bundesliga (ID: 2002)
- **Documentation**: [API Docs](https://docs.football-data.org/)

## 🆘 Support

For issues with:
- **Render deployment**: Check [Render docs](https://render.com/docs)
- **Football data**: Visit [football-data.org](https://www.football-data.org/)
- **Django issues**: See [Django documentation](https://docs.djangoproject.com/)

## 📋 Next Steps

1. Change admin password
2. Set up regular sync schedule (bookmark the sync dashboard)
3. Create game pools for users
4. Customize team colors in the sync_teams command
5. Add email notifications (optional)

---

Remember: Since you're on Render's free plan, you'll need to manually sync data through the web dashboard. Consider upgrading to a paid plan for cron job support if you want automatic updates.
