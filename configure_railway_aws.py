#!/usr/bin/env python3
"""
Railway AWS RDS Configuration Helper
This script helps configure Railway with AWS RDS connection
"""

import json
import os

def generate_railway_config():
    """Generate Railway configuration for AWS RDS"""
    
    print("🚀 Railway + AWS RDS Configuration Helper")
    print("=" * 50)
    
    # Get AWS RDS details
    print("\n📝 Enter your AWS RDS details:")
    rds_endpoint = input("RDS Endpoint: ").strip()
    db_username = input("Database Username (default: admin): ").strip() or "admin"
    db_password = input("Database Password: ").strip()
    db_name = input("Database Name (default: gaming_platform): ").strip() or "gaming_platform"
    secret_key = input("Flask Secret Key (or press Enter for generated): ").strip()
    
    if not secret_key:
        import secrets
        secret_key = secrets.token_urlsafe(32)
        print(f"🔑 Generated secret key: {secret_key}")
    
    # Create environment variables
    env_vars = {
        "FLASK_ENV": "production",
        "SECRET_KEY": secret_key,
        "MYSQL_HOST": rds_endpoint,
        "MYSQL_USER": db_username,
        "MYSQL_PASSWORD": db_password,
        "MYSQL_DB": db_name,
        "MYSQL_PORT": "3306",
        "PORT": "8080",
        "UPLOAD_FOLDER": "static/uploads",
        "MAX_CONTENT_LENGTH": "16777216"
    }
    
    # Display configuration
    print(f"\n📋 Railway Environment Variables Configuration:")
    print("=" * 60)
    print("Copy these to your Railway project → Variables tab:")
    print()
    
    for key, value in env_vars.items():
        print(f"{key}={value}")
    
    # Save to file
    env_file = "railway_env_vars.txt"
    with open(env_file, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"\n💾 Configuration saved to: {env_file}")
    
    # Railway JSON config
    railway_config = {
        "variables": env_vars,
        "build": {
            "builder": "DOCKERFILE"
        },
        "deploy": {
            "healthcheckPath": "/health",
            "healthcheckTimeout": 300,
            "restartPolicyType": "ON_FAILURE"
        }
    }
    
    # Save Railway JSON config
    with open("railway_config.json", 'w') as f:
        json.dump(railway_config, f, indent=2)
    
    print(f"💾 Railway config saved to: railway_config.json")
    
    # Generate deployment checklist
    print(f"\n✅ Deployment Checklist:")
    print("=" * 30)
    print("1. ✅ AWS RDS instance created and running")
    print("2. ⏳ RDS security group allows port 3306 access")
    print("3. ⏳ Database schema imported to RDS")
    print("4. ⏳ Environment variables added to Railway")
    print("5. ⏳ Railway app redeployed")
    print("6. ⏳ Health check passes at /health endpoint")
    
    # Test connection string
    print(f"\n🔌 Test your RDS connection:")
    print(f"mysql -h {rds_endpoint} -P 3306 -u {db_username} -p {db_name}")
    
    return env_vars

def verify_railway_deployment():
    """Helper to verify Railway deployment"""
    print(f"\n🔍 Railway Deployment Verification:")
    print("=" * 40)
    
    app_url = input("Enter your Railway app URL (e.g., https://your-app.railway.app): ").strip()
    
    if app_url:
        print(f"\n🧪 Test these endpoints:")
        print(f"1. Health Check: {app_url}/health")
        print(f"2. Database Debug: {app_url}/debug/db")
        print(f"3. Landing Page: {app_url}/")
        
        # Generate curl commands
        print(f"\n📡 cURL test commands:")
        print(f"curl {app_url}/health")
        print(f"curl {app_url}/debug/db")
    
    print(f"\n📊 Monitor your deployment:")
    print("- Railway Dashboard → Deployments → View Logs")
    print("- Check Build Logs for any errors")
    print("- Monitor Deploy Logs for startup issues")
    print("- Watch HTTP Logs for request handling")

def main():
    """Main configuration process"""
    try:
        # Generate Railway config
        env_vars = generate_railway_config()
        
        # Ask if user wants to verify deployment
        verify = input(f"\n❓ Do you want to verify deployment? (y/n): ").strip().lower()
        if verify in ['y', 'yes']:
            verify_railway_deployment()
        
        print(f"\n🎉 Configuration complete!")
        print(f"\n🚀 Next steps:")
        print("1. Go to Railway Dashboard → Your Project → Variables")
        print("2. Add each environment variable from above")
        print("3. Railway will auto-redeploy your app")
        print("4. Test your endpoints once deployment completes")
        
    except KeyboardInterrupt:
        print(f"\n\n👋 Configuration cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()