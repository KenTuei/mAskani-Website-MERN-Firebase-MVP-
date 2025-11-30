import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from apscheduler.schedulers.background import BackgroundScheduler

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()
scheduler = BackgroundScheduler()

# Firebase optional init
firebase = None
def init_firebase(cred_path=None):
    """Initialize Firebase only once."""
    global firebase
    try:
        import firebase_admin
        from firebase_admin import credentials

        if not firebase_admin._apps:
            cred_path = cred_path or os.getenv("FIREBASE_CRED_PATH", "firebase.json")
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase = firebase_admin.initialize_app(cred)
                print("Firebase initialized ✅")
            else:
                print(f"Firebase credential not found at {cred_path}. Skipping.")
        else:
            firebase = firebase_admin.get_app()
    except ImportError:
        print("firebase_admin not installed. Skipping Firebase init ⚠️")
    except Exception as e:
        print(f"Firebase init failed: {e}")
