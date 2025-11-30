import os
import logging
from datetime import datetime, timedelta

from flask import Flask, jsonify, redirect, request
from flask_jwt_extended import create_access_token, get_jwt_identity

from config import Config
from extensions import db, migrate, jwt, scheduler, init_firebase
from models import Role, User, Listing, Booking, Earnings, Payout, FcmToken

logger = logging.getLogger("maskani")
logging.basicConfig(level=logging.INFO)

# =========================================================
# APP CREATION
# =========================================================
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Firebase init (only when server runs)
    init_firebase()

    # Register routes (modular routes recommended)
    from routes import init_routes
    init_routes(app)

    return app

app = create_app()

# =========================================================
# UTILITIES
# =========================================================
def send_fcm_to_user(user_id, title, body):
    rec = FcmToken.query.filter_by(user_id=user_id).first()
    if rec:
        logger.info(f"[FCM] SEND TO {user_id} | {title}: {body}")
    else:
        logger.info(f"[FCM] No FCM token for user {user_id}")

def require_role(*roles):
    from functools import wraps
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            uid = request.headers.get("X-User-Id")
            user = None
            if uid:
                user = User.query.get(uid)
            else:
                identity = get_jwt_identity()
                if identity:
                    user = User.query.get(identity)
            if not user:
                return jsonify({"error": "Unauthorized"}), 401
            if user.role.name not in roles:
                return jsonify({"error": "Forbidden"}), 403
            request.current_user = user
            return fn(*args, **kwargs)
        return decorated
    return wrapper

# =========================================================
# HEALTH CHECK
# =========================================================
@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})

# =========================================================
# CRON JOBS
# =========================================================
def midnight_audit():
    logger.info("Running midnight audit...")
    tomorrow = (datetime.utcnow() + timedelta(days=1)).date()
    bookings = Booking.query.filter_by(status="confirmed").all()
    for b in bookings:
        if b.scheduled_slot and str(tomorrow) in b.scheduled_slot:
            send_fcm_to_user(b.hunter_id, "Viewing Reminder", "You have a viewing tomorrow.")
            send_fcm_to_user(b.listing.owner_id, "Viewing Reminder", "You have a viewing tomorrow.")

def weekly_payouts():
    logger.info("Running weekly payouts...")
    earnings = Earnings.query.filter(Earnings.balance > 0).all()
    for e in earnings:
        payout = Payout(leaser_id=e.leaser_id, amount=e.balance)
        db.session.add(payout)
        e.balance = 0.0
    db.session.commit()

# =========================================================
# CLI: INIT DB
# =========================================================
@app.cli.command("init-db")
def init_db():
    db.create_all()
    for role_name in ("hunter", "leaser", "admin"):
        if not Role.get_by_name(role_name):
            Role.create(role_name)
    if not User.query.filter_by(username="admin").first():
        admin_role = Role.get_by_name("admin")
        u = User(username="admin", email="admin@example.com", role_id=admin_role.id)
        u.set_password("adminpass")
        db.session.add(u)
        db.session.commit()
    print("Database initialized.")

# =========================================================
# RUN SERVER
# =========================================================
if __name__ == "__main__":
    from apscheduler.triggers.cron import CronTrigger

    # Add cron jobs
    scheduler.add_job(midnight_audit, CronTrigger(hour=0, minute=0))
    scheduler.add_job(weekly_payouts, CronTrigger(day_of_week="sun", hour=5))
    scheduler.start()

    app.run(debug=True)
