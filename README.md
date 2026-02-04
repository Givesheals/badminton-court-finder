# Badminton Court Finder

A web tool to find available badminton courts in Cambridge by aggregating availability from multiple sports facilities.

## Features

- **Hybrid Caching**: Automatically scrapes when data is stale, uses cache when fresh
- **Budget-Safe**: Rate limiting and daily scrape limits prevent runaway costs
- **Circuit Breaker**: Stops scraping after consecutive errors
- **REST API**: Simple API for querying court availability

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. Run database migration (if needed):
```bash
python migrate_db.py
```

4. Run the API:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Health Check
```
GET /health
```

### Get Availability
```
GET /api/availability?facility=Linton Village College&date=2026-02-06&start_time=15:00&end_time=18:00
```

Parameters:
- `facility` (required): Name of the facility
- `date` (optional): Filter by date (YYYY-MM-DD)
- `start_time` (optional): Filter by start time (HH:MM)
- `end_time` (optional): Filter by end time (HH:MM)

### List Facilities
```
GET /api/facilities
```

### Trigger Scrape
```
POST /api/scrape
Body: {"facility": "Linton Village College"}
```

## Configuration

Environment variables:
- `MAX_SCRAPES_PER_DAY`: Maximum scrapes per facility per day (default: 3)
- `MAX_SCRAPES_PER_HOUR`: Maximum scrapes per facility per hour (default: 1)
- `MIN_CACHE_AGE_SECONDS`: Minimum cache age before re-scraping (default: 3600 = 1 hour)
- `PORT`: Server port (default: 5000)
- `FLASK_DEBUG`: Enable debug mode (default: False)

## Deployment

### DigitalOcean App Platform

1. Push code to GitHub
2. Create new app in DigitalOcean
3. Connect GitHub repository
4. Use `app.yaml` configuration
5. Set environment variables (secrets) in DigitalOcean dashboard

### Docker

```bash
docker build -t badminton-court-finder .
docker run -p 5000:5000 --env-file .env badminton-court-finder
```

## Budget Safety Features

- **Daily Limits**: Max 3 scrapes per facility per day
- **Hourly Limits**: Max 1 scrape per facility per hour
- **Cache TTL**: 1 hour minimum cache age
- **Circuit Breaker**: Stops scraping after 3 consecutive errors
- **Graceful Degradation**: Returns cached data if scraping fails

## Project Structure

```
.
├── app.py                 # Flask API
├── scraper_manager.py     # Scraper with rate limiting
├── database.py            # Database models
├── scrapers/              # Facility-specific scrapers
│   └── linton_village_college.py
├── Dockerfile             # Docker configuration
├── app.yaml              # DigitalOcean config
└── requirements.txt      # Python dependencies
```

## Adding New Facilities

1. Create a new scraper in `scrapers/` directory
2. Add scraper class to `scraper_manager.py` in the `scrapers` dict
3. Follow the pattern from `linton_village_college.py`
