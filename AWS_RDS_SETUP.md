# AWS RDS Setup Guide for Gaming Platform

## 🎯 Step-by-Step AWS RDS MySQL Setup

### Prerequisites
- AWS Account (Free tier eligible)
- AWS CLI installed (optional)
- Your Railway app ready for deployment

---

## Step 1: Create AWS RDS MySQL Instance

### 1.1 Login to AWS Console
1. Go to [AWS Console](https://console.aws.amazon.com)
2. Navigate to **RDS** service
3. Click **"Create database"**

### 1.2 Database Engine Configuration
```
Engine Type: MySQL
Engine Version: MySQL 8.0.35 (latest)
Edition: MySQL Community
```

### 1.3 Templates
```
✅ Select: Free tier
```

### 1.4 Database Instance Settings
```
DB Instance Identifier: gaming-platform-db
Master Username: admin
Master Password: [Create a strong password - save this!]
```

### 1.5 Instance Configuration
```
DB Instance Class: db.t3.micro (Free tier eligible)
Storage Type: General Purpose SSD (gp2)
Allocated Storage: 20 GiB (Free tier maximum)
Storage Autoscaling: ❌ Disable (to stay in free tier)
```

### 1.6 Connectivity Settings
```
VPC: Default VPC
Subnet Group: default
Public Access: ✅ Yes (Important for Railway connection)
VPC Security Groups: Create new
  - Security Group Name: gaming-platform-sg
  - Port: 3306
```

### 1.7 Database Authentication
```
Database Authentication: Password authentication
```

### 1.8 Additional Configuration
```
Initial Database Name: gaming_platform
Backup Retention: 7 days
Backup Window: Default
Maintenance Window: Default
Auto Minor Version Upgrade: ✅ Enable
Deletion Protection: ❌ Disable (for testing)
```

---

## Step 2: Configure Security Group

### 2.1 Edit Security Group Rules
1. Go to **EC2** → **Security Groups**
2. Find **gaming-platform-sg**
3. Edit **Inbound Rules**

### 2.2 Add Railway Access Rules
```
Type: MySQL/Aurora
Protocol: TCP
Port: 3306
Source: 0.0.0.0/0  (For Railway access)
Description: Railway MySQL Access
```

**Note**: For production, restrict source to specific Railway IP ranges for better security.

---

## Step 3: Database Connection Details

### 3.1 Get RDS Endpoint
1. Go to **RDS** → **Databases**
2. Click on **gaming-platform-db**
3. Copy the **Endpoint** (looks like: gaming-platform-db.xxxxxxxxx.region.rds.amazonaws.com)

### 3.2 Connection Information
```
Host: gaming-platform-db.xxxxxxxxx.region.rds.amazonaws.com
Port: 3306
Username: admin
Password: [Your password]
Database: gaming_platform
```

---

## Step 4: Import Database Schema

### 4.1 Using MySQL Workbench
1. Download [MySQL Workbench](https://dev.mysql.com/downloads/workbench/)
2. Create new connection with RDS details
3. Open `complete_database_schema.sql`
4. Execute the script

### 4.2 Using Command Line
```bash
mysql -h gaming-platform-db.xxxxxxxxx.region.rds.amazonaws.com -P 3306 -u admin -p gaming_platform < complete_database_schema.sql
```

### 4.3 Using phpMyAdmin (Alternative)
1. Set up phpMyAdmin with RDS connection
2. Import SQL file through web interface

---

## Step 5: Configure Railway Environment Variables

### 5.1 Railway Dashboard
1. Go to your Railway project
2. Select your web service
3. Navigate to **"Variables"** tab

### 5.2 Add Environment Variables
```bash
FLASK_ENV=production
SECRET_KEY=your-super-secure-secret-key-change-this-immediately
MYSQL_HOST=gaming-platform-db.xxxxxxxxx.region.rds.amazonaws.com
MYSQL_USER=admin
MYSQL_PASSWORD=your-rds-password
MYSQL_DB=gaming_platform
MYSQL_PORT=3306
PORT=8080
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216
```

---

## Step 6: Test Connection

### 6.1 Deploy and Test
1. Railway will auto-redeploy after variable changes
2. Visit: `your-app.railway.app/health`
3. Check: `your-app.railway.app/debug/db`

### 6.2 Expected Results
```json
{
  "status": "success",
  "message": "Database connection successful",
  "database": "gaming_platform"
}
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Connection Timeout
**Problem**: Can't connect to RDS
**Solution**: 
- Check security group allows port 3306
- Verify public access is enabled
- Confirm endpoint URL is correct

#### 2. Access Denied
**Problem**: Authentication failed
**Solution**:
- Verify username/password
- Check database name exists
- Ensure user has proper permissions

#### 3. Railway Health Check Fails
**Problem**: App won't start
**Solution**:
- Check Railway deploy logs
- Verify all environment variables are set
- Test database connection locally first

### Debug Commands
```bash
# Test connection from local machine
mysql -h your-rds-endpoint.amazonaws.com -P 3306 -u admin -p -e "SHOW DATABASES;"

# Check Railway logs
railway logs

# Test specific endpoint
curl https://your-app.railway.app/debug/db
```

---

## 💰 Free Tier Limits

### AWS RDS Free Tier (12 months)
- **750 hours/month** of db.t3.micro usage
- **20 GB** of database storage
- **20 GB** of backup storage
- **10 million I/Os** per month

### Cost After Free Tier
- **db.t3.micro**: ~$13-15/month
- **Storage**: ~$2.30/month per 20GB
- **Backup**: $0.095/month per GB

---

## 🚀 Next Steps

1. **✅ Create RDS instance** following this guide
2. **✅ Configure security groups** for Railway access
3. **✅ Import database schema** using preferred method
4. **✅ Update Railway variables** with RDS connection
5. **✅ Test deployment** and verify functionality
6. **✅ Monitor usage** to stay within free tier

---

## 📞 Support

If you encounter issues:
1. Check AWS RDS documentation
2. Review Railway deployment logs
3. Test database connection independently
4. Verify all environment variables are correct

**Happy Deploying!** 🎮