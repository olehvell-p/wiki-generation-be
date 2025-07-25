# Heroku Deployment Guide

This guide will help you deploy the GitHub Repo Analyzer API to Heroku.

## Prerequisites

1. [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed
2. Git installed
3. Heroku account

## Files Added for Deployment

- `Procfile` - Tells Heroku how to run the application
- `runtime.txt` - Specifies Python version (3.11.0)
- Updated `requirements.txt` - Added gunicorn and psycopg2-binary for production
- `.env.example` - Template for environment variables

## Step-by-Step Deployment

### 1. Login to Heroku
```bash
heroku login
```

### 2. Create a New Heroku App
```bash
heroku create your-app-name
```

### 3. Add PostgreSQL Database
```bash
heroku addons:create heroku-postgresql:mini
```

### 4. Set Environment Variables

Set the required environment variables on Heroku:

```bash
# OpenAI API Key (required)
heroku config:set OPENAI_API_KEY=your_openai_api_key_here

# Optional: GitHub Token for private repos
heroku config:set GITHUB_TOKEN=your_github_token_here

# Optional: Set environment
heroku config:set ENVIRONMENT=production
```

**Note:** The `DATABASE_URL` is automatically set by the PostgreSQL addon.

### 5. Deploy to Heroku
```bash
git add .
git commit -m "Prepare for Heroku deployment"
git push heroku main
```

### 6. Run Database Migrations (if needed)
```bash
heroku run python -c "
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from src.database.config import init_db
asyncio.run(init_db())
"
```

### 7. Open Your App
```bash
heroku open
```

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (auto-set by Heroku) |
| `OPENAI_API_KEY` | Yes | Your OpenAI API key for AI functionality |
| `PORT` | No | Port number (auto-set by Heroku) |
| `GITHUB_TOKEN` | No | GitHub personal access token for private repos |
| `ENVIRONMENT` | No | Environment name (e.g., production) |

## Scaling

To scale your application:

```bash
# Scale web dynos
heroku ps:scale web=2

# Check current scaling
heroku ps
```

## Monitoring

View logs:
```bash
heroku logs --tail
```

## API Endpoints

Once deployed, your API will be available at:
- `https://your-app-name.herokuapp.com/analyze` - POST endpoint to analyze repositories
- `https://your-app-name.herokuapp.com/analyze/{uuid}` - GET endpoint for SSE analysis stream
- `https://your-app-name.herokuapp.com/repo/{uuid}/ask` - POST endpoint to ask questions about repositories

## Troubleshooting

### Common Issues

1. **Build Failures**: Check that all dependencies in `requirements.txt` are compatible
2. **Database Connection**: Ensure PostgreSQL addon is properly configured
3. **OpenAI API Issues**: Verify your API key is set correctly
4. **Port Issues**: Heroku automatically sets the PORT variable

### Checking Configuration
```bash
heroku config
```

### Restarting the App
```bash
heroku restart
```

## Local Testing with Production Settings

To test locally with production-like settings:

1. Copy `.env.example` to `.env`
2. Fill in your environment variables
3. Install dependencies: `pip install -r requirements.txt`
4. Run with gunicorn: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.router.main:app --bind 0.0.0.0:8000`

## Security Notes

- Never commit actual environment variables to version control
- Use strong passwords for database connections
- Regularly rotate API keys
- Monitor application logs for security issues 