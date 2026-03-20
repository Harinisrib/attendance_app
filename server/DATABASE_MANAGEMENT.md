# Database Management Guide

This guide explains how to properly manage the attendance application database.

## Database Manager Tool

The `db_manager.py` script provides comprehensive database management features.

### How to Use

```bash
cd server
python db_manager.py
```

## Features

### 1. Show Database Statistics
- View total users, classes, students, sessions
- See attendance records and rates
- Check risk distribution
- Monitor overall system health

### 2. Backup Database
- Creates timestamped backups automatically
- Stores backups in `backups/` folder
- Format: `attendance_backup_YYYYMMDD_HHMMSS.db`
- **Recommended**: Backup before any major changes

### 3. Restore Database
- Restore from any backup file
- Creates safety backup before restoring
- Useful for recovering from errors

### 4. Clean Orphaned Records
- Removes attendance records without students
- Removes sessions without classrooms
- Keeps database clean and efficient

### 5. Verify Database Integrity
- Checks all relationships are valid
- Identifies missing references
- Reports any data inconsistencies

## Best Practices

### Regular Backups
```bash
# Backup before important operations
python db_manager.py
# Choose option 2
```

### Weekly Maintenance
1. Run database statistics (option 1)
2. Verify integrity (option 5)
3. Clean orphaned records if needed (option 4)
4. Create backup (option 2)

### Before Major Changes
1. **Always backup first** (option 2)
2. Make your changes
3. Verify integrity (option 5)
4. Check statistics (option 1)

## Manual Database Operations

### View Database Directly
```bash
cd server/instance
sqlite3 attendance.db

# Useful SQLite commands:
.tables                    # List all tables
.schema table_name         # Show table structure
SELECT * FROM user;        # View users
SELECT * FROM classroom;   # View classes
SELECT * FROM student;     # View students
SELECT * FROM attendance;  # View attendance
.quit                      # Exit
```

### Manual Backup
```bash
cd server
cp instance/attendance.db instance/attendance_backup_manual.db
```

### Manual Restore
```bash
cd server
cp instance/attendance_backup_manual.db instance/attendance.db
```

## Database Structure

### Tables
- **user**: Faculty accounts
- **classroom**: Classes/courses
- **student**: Student records
- **class_session**: Session types (Morning, Afternoon, I, II, III, etc.)
- **attendance**: Attendance records

### Relationships
```
user (faculty)
  └── classroom (classes)
        ├── student (students)
        │     └── attendance (records)
        └── class_session (sessions)
```

## Troubleshooting

### Database Locked Error
- Close all connections to the database
- Stop the Flask server
- Run the operation again

### Integrity Issues
1. Run integrity check (option 5)
2. Clean orphaned records (option 4)
3. Verify again (option 5)

### Lost Data
1. Stop the server immediately
2. Check `backups/` folder for recent backup
3. Restore from backup (option 3)

## Backup Strategy

### Automatic Backups
The system creates `attendance.db.bak` automatically. Additional backups:

1. **Daily**: Use db_manager.py option 2
2. **Before Updates**: Manual backup
3. **After Major Changes**: Verify + backup

### Backup Locations
- `server/backups/` - Timestamped backups from db_manager
- `server/instance/attendance.db.bak` - System backup
- External storage - Copy important backups

## Safety Tips

✅ **DO:**
- Backup before major operations
- Verify integrity regularly
- Keep multiple backup copies
- Test restores occasionally

❌ **DON'T:**
- Delete backups without checking
- Modify database while server is running
- Skip integrity checks
- Ignore orphaned records

## Emergency Recovery

If database is corrupted:

1. **Stop the server**
   ```bash
   # Press Ctrl+C in server terminal
   ```

2. **Find latest backup**
   ```bash
   cd server/backups
   ls -lt  # Shows newest first
   ```

3. **Restore backup**
   ```bash
   python db_manager.py
   # Choose option 3
   # Enter backup file path
   ```

4. **Verify restoration**
   ```bash
   python db_manager.py
   # Choose option 1 (statistics)
   # Choose option 5 (integrity)
   ```

5. **Restart server**
   ```bash
   python app.py
   ```

## Contact

For database issues or questions, refer to this guide or check the main README.md
