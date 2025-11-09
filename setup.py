"""
Gaming Platform - Environment Setup Script
This script helps configure environment variables and checks setup
"""

import sys
import os
import shutil

def check_python_version():
    print("✓ Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  ✓ Python {version.major}.{version.minor} - OK")
        return True
    else:
        print(f"  ✗ Python {version.major}.{version.minor} - Need Python 3.8+")
        return False

def setup_environment():
    """Setup environment configuration"""
    print("\n✓ Setting up environment configuration...")
    
    # Check if .env exists
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("  ✓ Created .env file from .env.example")
        else:
            print("  ✗ .env.example not found!")
            return False
    else:
        print("  ✓ .env file already exists")
    
    # Load and validate configuration
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = [
            'SECRET_KEY',
            'MYSQL_HOST',
            'MYSQL_USER',  
            'MYSQL_PASSWORD',
            'MYSQL_DB',
            'RAZORPAY_KEY_ID',
            'RAZORPAY_KEY_SECRET'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print("\n  ⚠️ Missing environment variables:")
            for var in missing_vars:
                print(f"     - {var}")
            print("  📝 Please update your .env file")
            return False
        else:
            print("  ✓ All environment variables configured")
            return True
            
    except ImportError:
        print("  ⚠️ python-dotenv not installed, please run: pip install python-dotenv")
        return False

def check_dependencies():
    print("\n✓ Checking dependencies...")
    required = {
        'flask': 'Flask',
        'flask_mysqldb': 'Flask-MySQLdb', 
        'werkzeug': 'Werkzeug',
        'razorpay': 'razorpay',
        'dotenv': 'python-dotenv'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
            print(f"  ✓ {package} - Installed")
        except ImportError:
            print(f"  ✗ {package} - Missing")
            missing.append(package)
    
    if missing:
        print(f"\n  Install missing packages:")
        print(f"  pip install {' '.join(missing)}")
        return False
    return True

def check_directories():
    print("\n✓ Checking directory structure...")
    required_dirs = [
        'templates',
        'static',
        'static/uploads'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✓ {dir_path}/ - Exists")
        else:
            print(f"  ✗ {dir_path}/ - Missing (creating...)")
            os.makedirs(dir_path, exist_ok=True)
            all_exist = False
    
    return True

def check_files():
    print("\n✓ Checking required files...")
    required_files = {
        'app.py': 'Main application file',
        'database.sql': 'Database schema',
        'templates/base.html': 'Base template',
        'templates/landing.html': 'Landing page',
        'templates/signup.html': 'Signup page',
        'templates/login.html': 'Login page',
        'templates/home.html': 'Home page',
        'templates/room_details.html': 'Room details page',
        'templates/room_enrollments.html': 'Room enrollments page',
        'templates/profile.html': 'Profile page',
        'templates/admin_dashboard.html': 'Admin dashboard'
    }
    
    all_exist = True
    for file_path, description in required_files.items():
        if os.path.exists(file_path):
            print(f"  ✓ {file_path} - Exists")
        else:
            print(f"  ✗ {file_path} - Missing ({description})")
            all_exist = False
    
    return all_exist

def check_mysql_config():
    print("\n✓ Checking MySQL configuration...")
    print("  ⚠ Please verify in app.py:")
    print("    - MYSQL_HOST (line 12)")
    print("    - MYSQL_USER (line 13)")
    print("    - MYSQL_PASSWORD (line 14)")
    print("    - MYSQL_DB (line 15)")
    return True

def check_razorpay_config():
    print("\n✓ Checking Razorpay configuration...")
    print("  ⚠ Please verify in app.py:")
    print("    - RAZORPAY_KEY_ID (line 19)")
    print("    - RAZORPAY_KEY_SECRET (line 20)")
    return True

def test_mysql_connection():
    print("\n✓ Testing MySQL connection...")
    try:
        import MySQLdb
        print("  ✓ MySQLdb module available")
        print("  ⚠ Run the app to test actual connection")
        return True
    except ImportError:
        print("  ✗ MySQLdb not installed")
        print("  Install: pip install mysqlclient")
        return False

def create_requirements_txt():
    print("\n✓ Creating requirements.txt...")
    requirements = """Flask==2.3.0
Flask-MySQLdb==1.0.1
Werkzeug==2.3.0
razorpay==1.3.0
gunicorn==21.2.0
"""
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    print("  ✓ requirements.txt created")

def print_summary():
    print("\n" + "="*60)
    print("SETUP SUMMARY")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Configure MySQL in app.py (lines 12-15)")
    print("2. Configure Razorpay in app.py (lines 19-20)")
    print("3. Run database.sql in MySQL Workbench")
    print("4. Start the app: python app.py")
    print("5. Visit: http://localhost:5000")
    print("\n🔐 Default Admin Login:")
    print("Username: admin")
    print("Password: admin123")
    print("\n📚 For deployment, check README.md")
    print("="*60)

def main():
    print("="*60)
    print("GAMING PLATFORM - SETUP CHECK")
    print("="*60)
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_directories(),
        check_files(),
        check_mysql_config(),
        check_razorpay_config(),
        test_mysql_connection()
    ]
    
    create_requirements_txt()
    print_summary()
    
    if all(checks[:4]):  # First 4 checks must pass
        print("\n✅ Basic setup complete! Configure MySQL and Razorpay to continue.")
    else:
        print("\n⚠️ Some checks failed. Please fix the issues above.")

if __name__ == '__main__':
    main()
