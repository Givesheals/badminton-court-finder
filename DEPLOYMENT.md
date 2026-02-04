# Deployment Guide

## DigitalOcean App Platform

### Prerequisites
- DigitalOcean account
- GitHub repository with your code
- Environment variables set up

### Steps

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Initial deployment setup"
   git push origin main
   ```

2. **Create App in DigitalOcean**
   - Go to DigitalOcean App Platform
   - Click "Create App"
   - Connect your GitHub repository
   - Select the branch (usually `main`)

3. **Configure App**
   - Use the `app.yaml` file or configure manually:
     - **Build Command**: (auto-detected from Dockerfile)
     - **Run Command**: (auto-detected from Dockerfile)
     - **Port**: 5000
     - **Instance Size**: `basic-xxs` (smallest/cheapest)

4. **Set Environment Variables**
   In DigitalOcean dashboard, add these as **SECRETS**:
   - `LVC_USERNAME`: Your Linton Village College username
   - `LVC_PASSWORD`: Your Linton Village College password
   
   Optional (with defaults):
   - `MAX_SCRAPES_PER_DAY`: 3
   - `MAX_SCRAPES_PER_HOUR`: 1
   - `MIN_CACHE_AGE_SECONDS`: 3600
   - `PORT`: 5000
   - `FLASK_DEBUG`: False

5. **Deploy**
   - Click "Create Resources"
   - Wait for build and deployment (5-10 minutes)

6. **Set Budget Alerts**
   - Go to Billing → Budget Alerts
   - Set alerts at $10, $20, $50/month
   - Set hard limit if desired

### Cost Estimate
- **basic-xxs instance**: ~$5/month
- **Total**: ~$5-7/month for low usage

## Railway

### Steps

1. **Install Railway CLI** (optional)
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Create Project**
   - Go to railway.app
   - Create new project
   - Connect GitHub repo

3. **Configure**
   - Railway auto-detects Dockerfile
   - Set environment variables in dashboard
   - Deploy

4. **Set Budget Limits**
   - Go to Project Settings → Usage
   - Set spending limit

## Testing Locally

Before deploying, test locally:

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run migration
python migrate_db.py

# Test API
python app.py

# In another terminal, test endpoints:
curl http://localhost:5000/health
curl http://localhost:5000/api/facilities
curl "http://localhost:5000/api/availability?facility=Linton%20Village%20College&date=2026-02-06"
```

## Monitoring

### Check Logs
- DigitalOcean: App → Runtime Logs
- Railway: Deployments → View Logs

### Health Check
```bash
curl https://your-app-url.com/health
```

### Check Facility Stats
```bash
curl https://your-app-url.com/api/facility/Linton%20Village%20College/stats
```

## Troubleshooting

### Playwright Browser Issues
If Playwright fails in cloud:
- Ensure `playwright install chromium` runs in Dockerfile
- Check that system dependencies are installed

### Database Issues
- SQLite works for MVP
- For production, consider PostgreSQL (add to app.yaml)

### Rate Limiting
- Check facility stats endpoint to see scrape counts
- Adjust `MAX_SCRAPES_PER_DAY` if needed

## Budget Safety Checklist

- [ ] Set budget alerts in cloud platform
- [ ] Verify rate limiting is working (check logs)
- [ ] Test circuit breaker (trigger errors)
- [ ] Monitor first few days closely
- [ ] Set up logging/monitoring alerts
