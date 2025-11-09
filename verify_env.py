#!/usr/bin/env python3
"""
Environment Verification Script
Run this to verify your .env configuration is working properly
"""

import os
from dotenv import load_dotenv

def main():
    print("🔧 Environment Configuration Verification")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check critical variables
    variables = {
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'MYSQL_HOST': os.getenv('MYSQL_HOST'),
        'MYSQL_USER': os.getenv('MYSQL_USER'),
        'MYSQL_PASSWORD': os.getenv('MYSQL_PASSWORD'),
        'MYSQL_DB': os.getenv('MYSQL_DB'),
        'RAZORPAY_KEY_ID': os.getenv('RAZORPAY_KEY_ID'),
        'RAZORPAY_KEY_SECRET': os.getenv('RAZORPAY_KEY_SECRET'),
        'UPLOAD_FOLDER': os.getenv('UPLOAD_FOLDER'),
        'MAX_CONTENT_LENGTH': os.getenv('MAX_CONTENT_LENGTH')
    }
    
    print("\n📋 Environment Variables Status:")
    print("-" * 50)
    
    for key, value in variables.items():
        if value:
            if 'SECRET' in key or 'PASSWORD' in key:
                # Hide sensitive values
                display_value = f"***{value[-4:]}" if len(value) > 4 else "***"
            else:
                display_value = value
            print(f"✅ {key:<20}: {display_value}")
        else:
            print(f"❌ {key:<20}: NOT SET")
    
    # Test Flask app import
    print("\n🔍 Flask Application Test:")
    print("-" * 50)
    
    try:
        from app import app, RAZORPAY_KEY_ID
        print("✅ Flask app imports successfully")
        print(f"✅ Razorpay Key ID loaded: {RAZORPAY_KEY_ID[:10]}...")
        print("✅ Environment integration working!")
    except Exception as e:
        print(f"❌ Flask app import failed: {e}")
        return False
    
    # Check if upload folder exists
    upload_folder = os.getenv('UPLOAD_FOLDER', 'static/uploads')
    if os.path.exists(upload_folder):
        print(f"✅ Upload folder exists: {upload_folder}")
    else:
        print(f"⚠️ Upload folder missing: {upload_folder} (will be created automatically)")
    
    print("\n🎉 Environment verification completed!")
    print("\n📝 Next Steps:")
    print("1. Update your .env file with actual Razorpay keys")
    print("2. Configure MySQL database credentials")
    print("3. Run: python app.py")
    print("4. Visit: http://localhost:5000")
    
    return True

if __name__ == '__main__':
    main()