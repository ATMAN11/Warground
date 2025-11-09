# Deployment Checklist

## ✅ Pre-Deployment

- [ ] Code is working locally
- [ ] All dependencies in requirements.txt
- [ ] Environment variables configured
- [ ] Database schema ready
- [ ] Static files organized
- [ ] Upload folder structure created

## 🚀 Quick Deploy to Railway (Recommended)

### Step 1: Prepare Repository
```bash
# Initialize git if not already done
git init
git add .
git commit -m "Ready for deployment"
```

### Step 2: Push to GitHub
```bash
# Create repository on GitHub first, then:
git remote add origin https://github.com/yourusername/gaming-platform.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project"
4. Choose "Deploy from GitHub repo"
5. Select your repository
6. Railway will auto-deploy!

### Step 4: Add MySQL Database
1. In Railway dashboard, click "New"
2. Select "Database" → "Add MySQL"
3. Railway creates MySQL instance automatically

### Step 5: Configure Environment Variables
Go to your web service → Variables tab and add:
```
FLASK_ENV=production
SECRET_KEY=change-this-to-a-secure-random-string
MYSQL_HOST=mysql.railway.internal
MYSQL_USER=(copy from MySQL service variables)
MYSQL_PASSWORD=(copy from MySQL service variables)
MYSQL_DB=(copy from MySQL service variables)
PORT=8080
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
```

### Step 6: Setup Database
1. Connect to MySQL service in Railway
2. Import your `database.sql` file
3. Or run the setup script: `python setup_db.py`

### Step 7: Test Deployment
1. Railway provides a URL like: `https://yourapp.up.railway.app`
2. Visit the URL to test your application
3. Check logs if there are any issues

## 📋 Environment Variables Explained

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `production` |
| `SECRET_KEY` | Flask session security | `your-secure-key-here` |
| `MYSQL_HOST` | Database host | `mysql.railway.internal` |
| `MYSQL_USER` | Database username | `root` |
| `MYSQL_PASSWORD` | Database password | `generated-password` |
| `MYSQL_DB` | Database name | `gaming_platform` |
| `PORT` | Application port | `8080` |
| `RAZORPAY_KEY_ID` | Payment gateway ID | `rzp_test_xxxxx` |
| `RAZORPAY_KEY_SECRET` | Payment gateway secret | `secret_key_here` |

## 🔧 Alternative: Deploy to Render

### Step 1-2: Same as Railway (GitHub repo)

### Step 3: Deploy on Render
1. Go to [render.com](https://render.com)
2. Sign in with GitHub
3. Click "New" → "Web Service"
4. Connect your GitHub repository

### Step 4: Configure Render
```
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
Environment: Python 3
```

### Step 5: Add Database (PlanetScale)
1. Sign up at [planetscale.com](https://planetscale.com)
2. Create free database
3. Get connection string
4. Add as DATABASE_URL in Render

## 🗄️ Database Setup Options

### Option A: Import SQL File
1. Access database via web interface
2. Import `database.sql`
3. Verify tables created

### Option B: Run Setup Script
```bash
# In your deployment environment
python setup_db.py
```

### Option C: Manual Setup
1. Connect to database
2. Copy-paste SQL from `database.sql`
3. Execute statements

## 🚨 Troubleshooting

### Common Issues:

**App won't start:**
- Check logs for error messages
- Verify all environment variables are set
- Ensure requirements.txt is complete

**Database connection failed:**
- Verify database credentials
- Check if database service is running
- Ensure database exists

**Import errors:**
- Check Python version compatibility
- Verify all dependencies in requirements.txt
- Look for missing system dependencies

**Static files not loading:**
- Check file paths in templates
- Verify upload folder permissions
- Ensure static folder structure

### Getting Logs:
- **Railway:** Dashboard → Service → Logs tab
- **Render:** Dashboard → Service → Logs section
- **PythonAnywhere:** Error logs in Files tab

## 📊 Free Tier Limits

### Railway:
- $5 monthly credits
- Sleeps after inactivity
- 1GB RAM limit

### Render:
- 750 hours/month
- Sleeps after 15 min inactivity
- 512MB RAM

### PythonAnywhere:
- 1 web app
- 512MB storage
- Limited CPU seconds

## 🎯 Post-Deployment

- [ ] Test all major features
- [ ] Verify payment integration
- [ ] Check file upload functionality
- [ ] Test admin features
- [ ] Monitor performance
- [ ] Set up domain (if needed)

## 🔐 Security Notes

1. **Never commit sensitive data** to GitHub
2. **Use environment variables** for all secrets
3. **Generate strong secret keys** 
4. **Enable HTTPS** (automatic on most platforms)
5. **Regular database backups**

## 📈 Scaling Up

When your app grows beyond free tiers:
1. **Railway Pro:** $20/month for more resources
2. **Render Standard:** $7/month for always-on
3. **Dedicated hosting:** DigitalOcean, AWS, etc.

---

Your gaming platform is production-ready! 🎮🚀