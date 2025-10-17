## Deployment Guide

This guide covers deploying the Multiverse Inference Gateway to production.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Gateway](#running-the-gateway)
- [Process Management](#process-management)
- [Security Hardening](#security-hardening)
- [Monitoring](#monitoring)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended) or macOS
- **Python**: 3.11 or higher
- **Memory**: Minimum 512MB RAM, 1GB+ recommended
- **Disk**: 100MB for application + space for logs and database
- **Network**: Outbound HTTPS access to student servers

### Software Requirements

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# macOS (with Homebrew)
brew install python@3.11
```

## Installation

### 1. Create Deployment User (Linux only)

```bash
# Create dedicated user for running the gateway
sudo useradd -r -m -s /bin/bash gateway
sudo su - gateway
```

### 2. Clone Repository

```bash
cd /opt  # or your preferred location
git clone <repository-url> multiverse-gateway
cd multiverse-gateway
```

### 3. Set Up Virtual Environment

```bash
python3.11 -m venv env
source env/bin/activate
```

### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Create Configuration

```bash
cp .env.example .env
```

Edit `.env` and configure:

```bash
# Security - REQUIRED
ADMIN_API_KEY="your-very-secure-random-string-min-32-chars"

# Server settings
HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=INFO
ENABLE_FILE_LOGGING=true
ENABLE_CONSOLE_LOGGING=true

# Database
DATABASE_URL=sqlite+aiosqlite:///./gateway.db
DATABASE_WAL_MODE=true

# Health checking
HEALTH_CHECK_INTERVAL_SECONDS=60
MAX_CONSECUTIVE_FAILURES=3

# Request settings
REQUEST_TIMEOUT_SECONDS=300
MAX_RETRY_ATTEMPTS=2
```

### 6. Initialize Database

```bash
# The database will be created automatically on first run
# But you can test it:
python -c "import asyncio; from app.utils.database import init_database; asyncio.run(init_database())"
```

### 7. Test Installation

```bash
# Test that the app starts
./start.sh

# In another terminal, check health:
curl http://localhost:8000/health

# Stop the test:
./stop.sh
```

## Configuration

### Environment Variables

All configuration is done via environment variables in the `.env` file.

#### Security Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ADMIN_API_KEY` | ✅ | N/A | Admin API key (min 16 chars) |
| `REQUIRE_CLIENT_API_KEY` | ❌ | `false` | Require API key for inference |
| `CLIENT_API_KEYS` | ❌ | `[]` | List of valid client API keys |

#### Server Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HOST` | ❌ | `0.0.0.0` | Host to bind to |
| `PORT` | ❌ | `8000` | Port to bind to |
| `DEBUG` | ❌ | `false` | Enable debug mode |
| `RELOAD` | ❌ | `false` | Auto-reload on code changes |

#### Performance Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REQUEST_TIMEOUT_SECONDS` | ❌ | `300` | Backend request timeout |
| `MAX_RETRY_ATTEMPTS` | ❌ | `2` | Max failover retries |
| `MAX_REQUEST_BODY_SIZE` | ❌ | `1048576` | Max request size (bytes) |

#### Health Monitoring

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HEALTH_CHECK_INTERVAL_SECONDS` | ❌ | `60` | Check interval |
| `HEALTH_CHECK_TIMEOUT_SECONDS` | ❌ | `10` | Health check timeout |
| `MAX_CONSECUTIVE_FAILURES` | ❌ | `3` | Failures before unhealthy |
| `AUTO_DEREGISTER_AFTER_FAILURES` | ❌ | `true` | Auto-remove failed servers |

## Running the Gateway

### Using Startup Scripts (Recommended)

```bash
# Start
./start.sh

# Stop
./stop.sh
```

### Manual Start

```bash
source env/bin/activate
source .env
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Development Mode

```bash
# Enable auto-reload
RELOAD=true ./start.sh

# Or manually:
source env/bin/activate
source .env
python -m uvicorn app.main:app --reload
```

## Process Management

### Using systemd (Linux)

Create `/etc/systemd/system/multiverse-gateway.service`:

```ini
[Unit]
Description=Multiverse Inference Gateway
After=network.target

[Service]
Type=simple
User=gateway
WorkingDirectory=/opt/multiverse-gateway
Environment="PATH=/opt/multiverse-gateway/env/bin"
EnvironmentFile=/opt/multiverse-gateway/.env
ExecStart=/opt/multiverse-gateway/env/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/multiverse-gateway

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable multiverse-gateway
sudo systemctl start multiverse-gateway

# Check status
sudo systemctl status multiverse-gateway

# View logs
sudo journalctl -u multiverse-gateway -f
```

### Using supervisor (Alternative)

Install supervisor:

```bash
sudo apt install supervisor
```

Create `/etc/supervisor/conf.d/multiverse-gateway.conf`:

```ini
[program:multiverse-gateway]
command=/opt/multiverse-gateway/env/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
directory=/opt/multiverse-gateway
user=gateway
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/multiverse-gateway.log
environment=PATH="/opt/multiverse-gateway/env/bin"
```

Start:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start multiverse-gateway
```

## Security Hardening

### 1. Use Strong API Keys

```bash
# Generate secure API key (32+ characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Firewall Configuration

```bash
# Ubuntu/Debian with ufw
sudo ufw allow 8000/tcp
sudo ufw enable

# Or use iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

### 3. Reverse Proxy (nginx)

Install nginx:

```bash
sudo apt install nginx
```

Create `/etc/nginx/sites-available/multiverse-gateway`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # For streaming support
        proxy_buffering off;
        proxy_cache off;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/multiverse-gateway /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. HTTPS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 5. File Permissions

```bash
# Secure the .env file
chmod 600 .env

# Secure database
chmod 600 gateway.db

# Secure logs directory
chmod 750 logs/
```

## Monitoring

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Check from external monitoring
curl -f http://your-domain.com/health || echo "Gateway down!"
```

### Log Monitoring

```bash
# Tail application logs
tail -f logs/gateway.log

# Search for errors
grep ERROR logs/gateway.log

# Monitor in real-time
tail -f logs/gateway.log | grep -E "(ERROR|WARNING|CRITICAL)"
```

### Server Statistics

```bash
# Get gateway stats (requires admin API key)
curl -H "X-API-Key: your-admin-key" http://localhost:8000/admin/stats
```

### Performance Metrics

Monitor:
- Response times
- Request success rate
- Server health status
- Database size
- Log file size

## Backup & Recovery

### Database Backup

```bash
#!/bin/bash
# backup.sh - Daily database backup script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/multiverse-gateway"
DB_FILE="gateway.db"

mkdir -p $BACKUP_DIR

# SQLite backup
sqlite3 $DB_FILE ".backup $BACKUP_DIR/gateway_$DATE.db"

# Compress
gzip $BACKUP_DIR/gateway_$DATE.db

# Keep only last 7 days
find $BACKUP_DIR -name "gateway_*.db.gz" -mtime +7 -delete

echo "Backup completed: gateway_$DATE.db.gz"
```

Schedule with cron:

```bash
# Add to crontab
0 2 * * * /opt/multiverse-gateway/backup.sh
```

### Recovery

```bash
# Stop the gateway
./stop.sh

# Restore from backup
gunzip -c /opt/backups/multiverse-gateway/gateway_20250116.db.gz > gateway.db

# Restart
./start.sh
```

## Troubleshooting

### Gateway Won't Start

**Check logs:**
```bash
tail -50 logs/gateway.log
```

**Common issues:**
1. Port already in use: Change `PORT` in `.env`
2. Missing API key: Set `ADMIN_API_KEY` in `.env`
3. Database locked: Stop all gateway instances
4. Permission errors: Check file ownership

### High Memory Usage

Monitor memory:
```bash
ps aux | grep uvicorn
```

Optimize:
- Reduce `HEALTH_CHECK_INTERVAL_SECONDS`
- Limit concurrent connections
- Enable database WAL mode

### Slow Responses

Check:
1. Backend server health
2. Network latency to backends
3. Database query performance
4. Log file size (enable rotation)

Debug:
```bash
# Enable debug logging
LOG_LEVEL=DEBUG ./start.sh

# Monitor request timings
tail -f logs/gateway.log | grep "duration_ms"
```

### Database Issues

Reset database:
```bash
# Backup first!
cp gateway.db gateway.db.backup

# Remove and reinitialize
rm gateway.db
./start.sh
# Database will be recreated
```

### Health Checker Not Running

Check:
```bash
# View logs for health checker startup
grep "health" logs/gateway.log

# Verify it's checking servers
grep "Health check" logs/gateway.log
```

## Production Checklist

Before going live:

- [ ] Set strong `ADMIN_API_KEY` (32+ characters)
- [ ] Configure proper `LOG_LEVEL` (INFO or WARNING)
- [ ] Enable file logging
- [ ] Set up log rotation
- [ ] Configure database backups
- [ ] Set up process supervisor (systemd/supervisor)
- [ ] Configure firewall
- [ ] Set up reverse proxy (nginx)
- [ ] Enable HTTPS
- [ ] Test health endpoint
- [ ] Test admin endpoints with API key
- [ ] Test inference endpoints
- [ ] Monitor logs for errors
- [ ] Set up monitoring/alerting
- [ ] Document recovery procedures

## Performance Tuning

### For High Traffic

```bash
# Increase uvicorn workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Adjust timeouts
REQUEST_TIMEOUT_SECONDS=60
HEALTH_CHECK_TIMEOUT_SECONDS=5
```

### For Many Servers

```bash
# Reduce health check frequency
HEALTH_CHECK_INTERVAL_SECONDS=120

# Increase max failures threshold
MAX_CONSECUTIVE_FAILURES=5
```

## Support

For deployment issues:
1. Check logs in `logs/gateway.log`
2. Review this deployment guide
3. Check the troubleshooting section
4. Contact system administrator

## Additional Resources

- Main README: [README.md](README.md)
- API Documentation: http://localhost:8000/docs
- Configuration Reference: [.env.example](.env.example)
- Example Scripts: [examples/](examples/)
