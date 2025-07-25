#!/bin/bash

# Heroku Deployment Script for GitHub Repo Analyzer API

echo "🚀 Starting Heroku deployment process..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI is not installed. Please install it first:"
    echo "   https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if user is logged in to Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "❌ You are not logged in to Heroku. Please run 'heroku login' first."
    exit 1
fi

# Get app name from user
read -p "Enter your Heroku app name (or press Enter to create a new one): " APP_NAME

if [ -z "$APP_NAME" ]; then
    echo "📝 Creating a new Heroku app..."
    APP_NAME=$(heroku create --json | jq -r '.name')
    echo "✅ Created app: $APP_NAME"
else
    echo "📝 Using existing app: $APP_NAME"
fi

# Add PostgreSQL addon
echo "📦 Adding PostgreSQL database..."
heroku addons:create heroku-postgresql:mini --app $APP_NAME

# Set environment variables
echo "🔧 Setting up environment variables..."

read -p "Enter your OpenAI API key: " OPENAI_API_KEY
heroku config:set OPENAI_API_KEY="$OPENAI_API_KEY" --app $APP_NAME

read -p "Enter your GitHub token (optional, press Enter to skip): " GITHUB_TOKEN
if [ ! -z "$GITHUB_TOKEN" ]; then
    heroku config:set GITHUB_TOKEN="$GITHUB_TOKEN" --app $APP_NAME
fi

heroku config:set ENVIRONMENT=production --app $APP_NAME

# Deploy to Heroku
echo "🚀 Deploying to Heroku..."
git add .
git commit -m "Deploy to Heroku: $(date)"

# Add heroku remote if it doesn't exist
if ! git remote get-url heroku &> /dev/null; then
    heroku git:remote -a $APP_NAME
fi

git push heroku main

# Initialize database
echo "🗄️ Initializing database..."
heroku run python -c "
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from src.database.config import init_db
asyncio.run(init_db())
" --app $APP_NAME

echo "✅ Deployment complete!"
echo "🌐 Your API is available at: https://$APP_NAME.herokuapp.com"
echo "📊 View logs: heroku logs --tail --app $APP_NAME"
echo "⚙️  Manage app: https://dashboard.heroku.com/apps/$APP_NAME" 