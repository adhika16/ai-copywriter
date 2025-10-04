#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Navigate to the theme directory and install npm dependencies
echo "Installing frontend dependencies..."
cd /app/theme/static_src
npm install
cd /app

# Run Tailwind CSS build
echo "Building Tailwind CSS..."
python manage.py tailwind build

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input --clear

# Debug: Check if CSS file was generated and collected
echo "Checking if CSS file exists..."
ls -la /app/theme/static/css/dist/ || echo "CSS dist directory not found"
ls -la /app/staticfiles/css/dist/ || echo "Staticfiles CSS dist directory not found"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Start Gunicorn server
echo "Starting Gunicorn server..."
exec "$@"
