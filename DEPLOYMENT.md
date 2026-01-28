# Deployment Guide - H2 System

## Production Deployment Checklist

### Pre-Deployment

- [ ] Update SECRET_KEY in config.py
- [ ] Set FLASK_ENV=production
- [ ] Disable debug mode (DEBUG=False)
- [ ] Change default admin password
- [ ] Review all security settings
- [ ] Test all features in development
- [ ] Backup production data

---

## Local Development Setup

### 1. Initial Setup
```bash
# Clone repository
git clone <repo-url>
cd h2sqrr

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Initialize database
python run.py
```

### 2. Seed Sample Data (Optional)
```bash
python cli.py seed_db
```

### 3. Access Application
- URL: http://localhost:5000
- Username: admin
- Password: admin

---

## Production Deployment

### Using Gunicorn (Recommended)

#### 1. Install Gunicorn
```bash
pip install gunicorn
```

#### 2. Run with Gunicorn
```bash
# Basic
gunicorn -w 4 -b 0.0.0.0:5000 run:app

# With logging
gunicorn -w 4 -b 0.0.0.0:5000 \
  --access-logfile /var/log/h2system/access.log \
  --error-logfile /var/log/h2system/error.log \
  run:app

# Daemonized
gunicorn -w 4 -b 0.0.0.0:5000 \
  --daemon \
  --pid /var/run/h2system.pid \
  run:app
```

### Using Docker

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . .

ENV FLASK_ENV=production
ENV FLASK_DEBUG=False

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

#### Build and Run
```bash
# Build image
docker build -t h2system:latest .

# Run container
docker run -d \
  -p 5000:5000 \
  -v h2system_db:/app/instance \
  -e FLASK_ENV=production \
  --name h2system \
  h2system:latest
```

### Using Systemd (Linux)

#### 1. Create Service File
```bash
sudo nano /etc/systemd/system/h2system.service
```

#### 2. Service Configuration
```ini
[Unit]
Description=H2 System - Health & Hostel Management
After=network.target

[Service]
Type=notify
User=h2user
Group=h2user
WorkingDirectory=/home/h2user/h2sqrr
Environment="PATH=/home/h2user/h2sqrr/venv/bin"
ExecStart=/home/h2user/h2sqrr/venv/bin/gunicorn \
  -w 4 \
  -b 0.0.0.0:5000 \
  -n h2system \
  run:app
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 3. Enable Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable h2system
sudo systemctl start h2system
sudo systemctl status h2system
```

---

## Nginx Configuration

### Reverse Proxy Setup

```nginx
upstream h2_app {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name h2system.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name h2system.yourdomain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/h2system.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/h2system.yourdomain.com/privkey.pem;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 20M;

    location / {
        proxy_pass http://h2_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
        proxy_request_buffering off;
    }

    location /static/ {
        alias /home/h2user/h2sqrr/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
```

---

## Database Setup

### SQLite (Development/Small Deployments)
```bash
# Already configured
# Database file: h2_system.db
```

### PostgreSQL (Production)

#### 1. Install Dependencies
```bash
pip install psycopg2-binary
```

#### 2. Update config.py
```python
import os
DATABASE_URL = os.environ.get('DATABASE_URL') or \
    'postgresql://user:password@localhost/h2system'
```

#### 3. Set Environment Variable
```bash
export DATABASE_URL="postgresql://h2user:password@localhost/h2system"
```

#### 4. Create Database
```bash
sudo -u postgres createdb h2system
sudo -u postgres createuser h2user
```

---

## Security Hardening

### 1. Environment Variables
```bash
# Update .env with production values
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<generate-new-secret-key>
DATABASE_URL=<production-db-url>
```

### 2. Generate Secure Secret Key
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. File Permissions
```bash
# Set appropriate permissions
chmod 640 .env
chmod 755 h2sqrr/
chmod 644 h2sqrr/*.py
chmod 755 h2sqrr/app/
```

### 4. Update Admin Password
```python
# After deployment, login and change admin password
# Users → Edit User (for admin)
```

### 5. Enable HTTPS
- Use Let's Encrypt for free SSL certificates
- Configure with Nginx/Apache
- Force HTTPS redirect

### 6. Firewall Configuration
```bash
# Open necessary ports
sudo ufw allow 22/tcp     # SSH
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw deny 5000/tcp    # Block Flask port
```

---

## Backups & Maintenance

### Database Backups

#### SQLite
```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/h2system"
DATE=$(date +%Y%m%d_%H%M%S)
cp /home/h2user/h2sqrr/h2_system.db $BACKUP_DIR/h2_system_$DATE.db
# Keep last 30 days
find $BACKUP_DIR -mtime +30 -delete
```

#### PostgreSQL
```bash
# Backup command
pg_dump h2system > h2system_$(date +%Y%m%d).sql

# Restore command
psql h2system < h2system_20260128.sql
```

#### Cron Job (Daily Backup)
```bash
# Add to crontab -e
0 2 * * * /home/h2user/backup_h2system.sh
```

### Log Monitoring
```bash
# View application logs
tail -f /var/log/h2system/error.log
tail -f /var/log/h2system/access.log

# Monitor system resources
htop
iostat -x 1 5
```

---

## Performance Optimization

### 1. Database Optimization
- Create indexes on frequently queried columns
- Use query profiling to identify slow queries
- Archive old data periodically

### 2. Caching
- Implement Redis for session caching
- Cache frequently accessed data
- Use browser caching for static files

### 3. Load Balancing
```nginx
upstream h2_backend {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}
```

### 4. Static Files
- Serve static files from CDN
- Use gzip compression
- Minify CSS/JavaScript

---

## Troubleshooting

### Application won't start
```bash
# Check for syntax errors
python -m py_compile app/*.py

# Check dependencies
pip install -r requirements.txt --upgrade

# Check logs
journalctl -u h2system -n 50
```

### Database connection error
```bash
# Test connection
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.session.execute('SELECT 1')"

# Check database permissions
ls -la h2_system.db
```

### High CPU usage
- Increase worker processes
- Implement caching
- Optimize database queries
- Monitor slow endpoints

### Out of memory
- Reduce worker processes
- Enable database connection pooling
- Implement memory profiling
- Archive old data

---

## Monitoring & Alerts

### Application Monitoring
```bash
# Install monitoring tools
pip install prometheus-client

# Add to application for metrics
# CPU, memory, request count, response time
```

### Health Check Endpoint
```python
@app.route('/health')
def health():
    return {'status': 'healthy'}, 200
```

### Email Alerts
- Configure error notifications
- Monitor disk space
- Track failed logins

---

## Upgrade & Rollback

### Backup Before Upgrade
```bash
# Backup database and code
cp -r h2sqrr h2sqrr_backup_$(date +%Y%m%d)
pg_dump h2system > h2system_$(date +%Y%m%d).sql
```

### Update Application
```bash
# Pull new code
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run migrations (if any)
python run.py

# Restart service
sudo systemctl restart h2system
```

### Rollback If Issues
```bash
# Restore from backup
rm -rf h2sqrr
cp -r h2sqrr_backup_20260128 h2sqrr

# Restart service
sudo systemctl restart h2system
```

---

## Maintenance Schedule

| Task | Frequency |
|------|-----------|
| Database backup | Daily |
| Log rotation | Weekly |
| Security updates | As needed |
| Dependency updates | Monthly |
| Full backup | Weekly |
| Performance audit | Monthly |

---

## Support & Resources

- **Documentation**: See README.md
- **Quick Start**: See QUICKSTART.md
- **Issues**: Check error logs
- **Database**: See models.py for schema

---

**Last Updated**: January 2026  
**Status**: Production Ready
