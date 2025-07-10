#!/bin/bash
# Auto Scouter Backup System
BACKUP_DIR="/home/elo/backups/auto_scouter"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Database backup
pg_dump "postgresql://auto_scouter_user:OzXZ3bYnqxPx8LQk6SUNb7fTt5r70ZTRsc0lPfGMvx8=@localhost:5432/auto_scouter_prod" > "$BACKUP_DIR/db_backup_$DATE.sql"

# Application backup
tar -czf "$BACKUP_DIR/app_backup_$DATE.tar.gz" -C /home/elo/zio auto_scouter --exclude="*.log" --exclude="venv_new"

# Cleanup old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "$(date): Backup completed successfully" >> /var/log/auto_scouter/backup.log
