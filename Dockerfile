# Use a single stage for the build
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Node.js, npm, and MySQL client dependencies
RUN apt-get update && apt-get install -y \
    curl \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY requirements.txt .
COPY theme/static_src/package.json theme/static_src/package-lock.json ./theme/static_src/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Create logs directory
RUN mkdir -p logs

# Expose the port the app runs on
EXPOSE 8000

# Run the application
ENTRYPOINT ["entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "ai_copywriter.wsgi:application"]