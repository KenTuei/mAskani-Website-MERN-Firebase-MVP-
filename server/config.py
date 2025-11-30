import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

class Config:
    # Flask / JWT / Database
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key")
    
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///maskani.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Timezone / Payment Config
    TIMEZONE = os.getenv("TIMEZONE", "Africa/Nairobi")
    
    # Stripe
    STRIPE_SECRET = os.getenv("STRIPE_SECRET", "")

    # M-Pesa / Daraja
    MPESA_CONSUMER_KEY = os.getenv("CONSUMER_KEY", "")
    MPESA_CONSUMER_SECRET = os.getenv("CONSUMER_SECRET", "")
    MPESA_BUSINESS_SHORT_CODE = os.getenv("SHORTCODE", "")
    MPESA_PASS_KEY = os.getenv("PASSKEY", "")
    
    BASE_CALLBACK_URL = os.getenv("BASE_CALLBACK_URL", "")
    MPESA_CALLBACK_URL = f"{BASE_CALLBACK_URL}/api/mpesa/callback" if BASE_CALLBACK_URL else ""

    MPESA_ENV = os.getenv("MPESA_ENV", "sandbox").lower()
    if MPESA_ENV == "production":
        MPESA_STK_PUSH_URL = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        MPESA_TOKEN_URL = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    else:
        MPESA_STK_PUSH_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        MPESA_TOKEN_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
