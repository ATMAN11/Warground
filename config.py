import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key-change-this')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Database Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '1111')
    MYSQL_DB = os.getenv('MYSQL_DB', 'gaming_platform')
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # 16MB
    
    # Razorpay Configuration
    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')
    
    # Application Settings
    APP_NAME = os.getenv('APP_NAME', 'Gaming Platform')
    
    @staticmethod
    def validate_config():
        """Validate required configuration"""
        errors = []
        
        if not Config.RAZORPAY_KEY_ID:
            errors.append("RAZORPAY_KEY_ID is required")
        if not Config.RAZORPAY_KEY_SECRET:
            errors.append("RAZORPAY_KEY_SECRET is required")
        if not Config.MYSQL_PASSWORD:
            errors.append("MYSQL_PASSWORD should be set")
            
        return errors

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}