# Deployment Guide - H2 System

## Production Deployment Checklist

### Pre-Deployment

- [ ] Set up PostgreSQL database (production)
- [ ] Update DATABASE_URL for PostgreSQL
- [ ] Change default admin password
- [ ] Create initial database backup

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

# Install dependencies (includes psycopg2 for PostgreSQL)
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# For development: SQLite (default)
# For production: Update DATABASE_URL in .env to PostgreSQL connection string
# DATABASE_URL=postgresql://h2user:password@localhost:5432/h2system

# Initialize database and create tables
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
- **Note**: Equipment system initializes with 12 sample items on first run

---

## Production Deployment

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

## Database Setup

### PostgreSQL

#### 1. Install PostgreSQL
**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 2. Create Database and User
```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Inside psql:
CREATE DATABASE h2system;
CREATE USER h2user WITH PASSWORD 'secure_password_here';
ALTER ROLE h2user SET client_encoding TO 'utf8';
ALTER ROLE h2user SET default_transaction_isolation TO 'read committed';
ALTER ROLE h2user SET default_transaction_deferrable TO on;
ALTER ROLE h2user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE h2system TO h2user;
\q
```

#### 3. Install Python Dependencies
```bash
pip install psycopg2-binary
```

#### 4. Update .env File
```bash
# Database Configuration
DATABASE_URL=postgresql://h2user:secure_password_here@localhost:5432/h2system
```
#### 5. Verify Connection
```bash
# Test connection
python -c "import psycopg2; conn = psycopg2.connect('postgresql://h2user:secure_password_here@localhost/h2system'); print('Connection successful'); conn.close()"
```

---

## Backups & Maintenance

### Database Backups

#### PostgreSQL

**Full Database Backup:**
```bash
# Plain SQL format (text)
pg_dump -U h2user -h localhost h2system > h2system_$(date +%Y%m%d_%H%M%S).sql

# Custom format (compressed, better for large databases)
pg_dump -U h2user -h localhost -F c h2system > h2system_$(date +%Y%m%d_%H%M%S).dump
```

**Restore from Backup:**
```bash
# From SQL file
psql -U h2user -h localhost -d h2system < h2system_20260128.sql

# From dump file (compressed format)
pg_restore -U h2user -h localhost -d h2system h2system_20260128.dump
```

**Automated Backup Script:**
```bash
#!/bin/bash
BACKUP_DIR="/backups/h2system"
DB_USER="h2user"
DB_HOST="localhost"
DB_NAME="h2system"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U $DB_USER -h $DB_HOST -F c $DB_NAME > $BACKUP_DIR/h2system_$DATE.dump

# Compress backup
gzip $BACKUP_DIR/h2system_$DATE.dump

# Keep backups for 30 days
find $BACKUP_DIR -name "h2system_*.dump.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/h2system_$DATE.dump.gz"
```

#### SQLite (Development Only)
```bash
# Simple file copy (development only)
cp /path/to/h2_system.db /backups/h2_system_$(date +%Y%m%d).db
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

### PostgreSQL connection errors
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check PostgreSQL is listening on port 5432
sudo ss -tlnp | grep 5432

# Test psql connection
psql -U h2user -h localhost -d h2system -c "SELECT 1;"

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql.log

# Check pg_hba.conf for authentication method
sudo cat /etc/postgresql/13/main/pg_hba.conf

# Restart PostgreSQL if needed
sudo systemctl restart postgresql
```

### Database is locked or slow
```bash
# Check active connections in PostgreSQL
psql -U h2user -d h2system -c "SELECT pid, usename, application_name, state FROM pg_stat_activity;"

# Find long-running queries
psql -U h2user -d h2system -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"

# Kill idle connections
psql -U h2user -d h2system -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"

# Analyze and vacuum database
psql -U h2user -d h2system -c "VACUUM ANALYZE;"
```

---

## Support & Resources

- **Documentation**: See README.md
- **Quick Start**: See QUICKSTART.md
- **Issues**: Check error logs or application logs
- **Database**: See models.py for schema

### PostgreSQL Resources
- [PostgreSQL Official Documentation](https://www.postgresql.org/docs/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [pgBouncer - Connection Pooling](https://www.pgbouncer.org/)
- [pgAdmin - Web Interface](https://www.pgadmin.org/)
- [pg_dump Documentation](https://www.postgresql.org/docs/current/app-pgdump.html)

### Useful Tools
- **pgAdmin**: Web interface for PostgreSQL management
- **DBeaver**: Universal database tool with PostgreSQL support
- **pgBouncer**: Connection pooling middleware
- **pg_stat_statements**: Query performance analysis
- **auto_explain**: Slow query logging

---

**Last Updated**: February 2026  
**Status**: Production Ready with PostgreSQL  
**Database**: PostgreSQL 13+ (Recommended)
