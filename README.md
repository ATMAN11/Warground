# 🎮 Gaming Platform

A Flask-based gaming tournament platform for PUBG/FreeFire with virtual coin economy, Razorpay payments, and admin-managed withdrawals.

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd gaming-platform

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your configuration
# Update the following values:
```

**Required Environment Variables:**

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-here
DEBUG=True

# Database Configuration  
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=gaming_platform

# Razorpay Configuration (Get from https://dashboard.razorpay.com/)
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxx
RAZORPAY_KEY_SECRET=your_razorpay_secret_key

# File Upload Configuration
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216
```

### 3. Database Setup

```bash
# Create MySQL database
mysql -u root -p
CREATE DATABASE gaming_platform;

# Import the schema
mysql -u root -p gaming_platform < database.sql
```

### 4. Run Setup Check

```bash
python setup.py
```

### 5. Start the Application

```bash
python app.py
```

Visit `http://localhost:5000` to access the platform.

## 🔐 Default Admin Login

- **Username:** `admin`
- **Password:** `admin123`

## 💰 Razorpay Integration

### Getting Razorpay Keys

1. Visit [Razorpay Dashboard](https://dashboard.razorpay.com/)
2. Create an account or login
3. Go to Settings → API Keys
4. Generate API keys for Test/Live mode
5. Update your `.env` file with these keys

### Test Mode vs Live Mode

- **Test Mode:** Use `rzp_test_` prefixed keys for development
- **Live Mode:** Use `rzp_live_` prefixed keys for production

## 🏗️ Project Structure

```
gaming-platform/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── setup.py              # Setup and validation script
├── requirements.txt      # Python dependencies
├── database.sql          # MySQL schema
├── .env                  # Environment variables (create from .env.example)
├── .env.example          # Environment template
├── .gitignore           # Git ignore rules
├── templates/           # Jinja2 HTML templates
│   ├── base.html        # Base template with navigation
│   ├── home.html        # Room listings
│   ├── profile.html     # User profile with Razorpay
│   ├── room_details.html
│   └── ...
└── static/
    └── uploads/         # Payment screenshots storage
```

## 🎯 Key Features

### User Features
- **Team Management:** Create and manage gaming teams
- **Tournament Enrollment:** Join rooms with team-based entry
- **Virtual Wallet:** Razorpay-powered coin system
- **Real-time Updates:** Dynamic coin balance updates
- **Withdrawal System:** Cash-out with admin approval

### Admin Features  
- **Room Management:** Create tournaments with flexible settings
- **Kill Tracking:** Record player kills with reward system
- **Payment Approval:** Manage withdrawal requests
- **User Management:** Monitor platform activity

## 🔧 Configuration Options

### Flask Settings
```env
SECRET_KEY=your-secret-key          # Session encryption key
DEBUG=True                          # Development mode
```

### Database Settings
```env
MYSQL_HOST=localhost                # Database host
MYSQL_USER=root                     # Database username
MYSQL_PASSWORD=password             # Database password
MYSQL_DB=gaming_platform           # Database name
```

### Payment Settings
```env
RAZORPAY_KEY_ID=rzp_test_xxx       # Razorpay public key
RAZORPAY_KEY_SECRET=secret_xxx      # Razorpay secret key
```

### File Upload Settings
```env
UPLOAD_FOLDER=static/uploads        # Upload directory
MAX_CONTENT_LENGTH=16777216         # Max file size (16MB)
```

## 🔄 Development Workflow

### Environment Management
```bash
# Load environment variables
python -c "from dotenv import load_dotenv; load_dotenv(); print('Environment loaded')"

# Validate configuration
python -c "from config import Config; Config.validate_config()"

# Run setup check
python setup.py
```

### Database Operations
```bash
# Backup database
mysqldump -u root -p gaming_platform > backup.sql

# Restore database  
mysql -u root -p gaming_platform < backup.sql
```

## 📝 Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Flask session encryption key | - | ✅ |
| `DEBUG` | Enable debug mode | `False` | ❌ |
| `MYSQL_HOST` | Database host | `localhost` | ✅ |
| `MYSQL_USER` | Database username | `root` | ✅ |
| `MYSQL_PASSWORD` | Database password | - | ✅ |
| `MYSQL_DB` | Database name | `gaming_platform` | ✅ |
| `RAZORPAY_KEY_ID` | Razorpay public key | - | ✅ |
| `RAZORPAY_KEY_SECRET` | Razorpay secret key | - | ✅ |
| `UPLOAD_FOLDER` | File upload directory | `static/uploads` | ❌ |
| `MAX_CONTENT_LENGTH` | Max upload size (bytes) | `16777216` | ❌ |

## 🚨 Security Best Practices

1. **Never commit `.env` file** to version control
2. **Use strong secret keys** for production
3. **Enable Razorpay live mode** only for production
4. **Set proper file permissions** on `.env` file
5. **Use environment-specific configuration**
6. **Regularly rotate API keys**

## 🐛 Troubleshooting

### Common Issues

**Missing Environment Variables:**
```bash
python setup.py  # Check configuration
```

**Database Connection Failed:**
- Verify MySQL is running
- Check credentials in `.env`
- Ensure database exists

**Razorpay Payment Failed:**
- Verify API keys are correct
- Check test/live mode consistency
- Ensure proper network connectivity

**File Upload Issues:**
- Check `UPLOAD_FOLDER` permissions
- Verify `MAX_CONTENT_LENGTH` setting
- Ensure disk space availability

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review environment configuration