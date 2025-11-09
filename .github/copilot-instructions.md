# Gaming Platform - AI Coding Agent Instructions

## Project Overview
A Flask-based gaming tournament platform for PUBG/FreeFire with virtual coin economy, Razorpay payments, and admin-managed withdrawals.

## Architecture

### Core Components
- **app.py**: Main Flask application with all routes and business logic
- **database.sql**: MySQL schema with 6 tables (users, pubg_usernames, rooms, enrollments, withdrawals, transactions)
- **templates/**: Jinja2 HTML templates extending `base.html` with Bootstrap 5
- **static/uploads/**: Payment screenshot storage

### Database Schema
- **users**: Authentication + coin wallet (GPay-linked)
- **pubg_usernames**: Multi-username support per user (1-to-many)
- **rooms**: Tournament rooms with entry fees and prize pools
- **enrollments**: Room registrations (deduct coins on enrollment)
- **withdrawals**: Cash-out requests (min 150 Rs, admin approval required)
- **transactions**: Payment audit trail

### Money Flow
1. User buys coins via Razorpay (INR → coins 1:1)
2. Coins deducted on room enrollment
3. Withdrawals require admin approval with GPay screenshot upload

## Critical Patterns

### Authentication
- **Plaintext passwords** in current implementation (⚠️ SECURITY ISSUE in app.py line 96: `user[2] == password`)
- `gaming_platform.py` has proper hashing with `generate_password_hash`/`check_password_hash`
- Session stores: `user_id`, `username`, `is_admin`
- Two decorators: `@login_required`, `@admin_required`

### Database Access
- **Direct cursor pattern** (no ORM):
  ```python
  cur = mysql.connection.cursor()
  cur.execute("SELECT ...")
  results = cur.fetchall()  # Returns tuples
  cur.close()
  ```
- Always use try/except with `mysql.connection.rollback()` on failures
- Template data passed as **tuples** indexed by position (e.g., `room[1]` = room_name)

### File Uploads
- Admin withdrawal approvals require screenshot
- Pattern: `secure_filename(f"{id}_{timestamp}.png")` → `static/uploads/`
- Max size: 16MB (configured in app.config)

## Development Workflow

### Environment Setup
```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Database Setup
1. Create MySQL database: `gaming_platform`
2. Run `database.sql` in MySQL Workbench or CLI
3. Configure in app.py lines 16-19:
   - MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

### Configuration Required
- **Secret key** (line 12): Change `'your-secret-key-change-this'`
- **Razorpay** (lines 23-24): Add real API keys
- **MySQL credentials** (lines 16-19): Match your local setup

### Running
```powershell
python app.py  # Runs on http://localhost:5000
```

Default admin: `admin` / `admin123` (from database.sql)

## Common Tasks

### Adding a Route
- Use `@login_required` for user pages, `@admin_required` for admin
- Flash messages: `flash('Message', 'success|danger|warning')`
- Always close cursor in `finally` block

### Template Changes
- All templates extend `templates/base.html`
- Bootstrap 5 classes used throughout
- Flash messages auto-displayed in base template
- Razorpay checkout.js loaded in base (line 37)

### Adding Database Columns
1. Update `database.sql`
2. Modify queries in app.py (cursor.execute)
3. Update tuple indexing in templates (e.g., `room[0]`, `room[1]`)

## Known Issues
1. **app.py uses plaintext passwords** (line 65, 96) - `gaming_platform.py` has correct implementation
2. No CSRF protection on forms
3. No input validation/sanitization
4. Hard-coded database credentials (should use environment variables)
5. No logging/monitoring

## File Locations
- Routes: `app.py`
- Schema: `database.sql`
- UI: `templates/*.html`
- Uploads: `static/uploads/`
- Dependencies: `requirements.txt`
