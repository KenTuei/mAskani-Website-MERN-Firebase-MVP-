import os
import json
import uuid
import random
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import DB & models
from models import (
    db,
    Role,
    User,
    Listing,
    Booking,
    Earnings,
    Payout,
    Payment,
    PaymentLog,
    FcmToken
)

# ---------------------------------------------------------
# APP CONFIG
# ---------------------------------------------------------
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///maskani.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

db.init_app(app)

logger = logging.getLogger("maskani")
logging.basicConfig(level=logging.INFO)

TIMEZONE = os.getenv("TIMEZONE", "Africa/Nairobi")
STRIPE_SECRET = os.getenv("STRIPE_SECRET", "")
MPESA_KEY = os.getenv("MPESA_KEY", "")
MPESA_SECRET = os.getenv("MPESA_SECRET", "")


# =========================================================
# UTILITIES + AUTH
# =========================================================

def send_fcm_to_user(user_id, title, body):
    """Stub for FCM - printing to console."""
    rec = FcmToken.query.filter_by(user_id=user_id).first()
    if rec:
        logger.info(f"[FCM] SEND TO {user_id} | {title}: {body}")
    else:
        logger.info(f"[FCM] No FCM token for user {user_id}")


def require_role(*roles):
    """
    Fake auth using X-User-Id header.
    Example:
        X-User-Id: 1
    Real version should be JWT-based.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            uid = request.headers.get("X-User-Id")
            if not uid:
                return jsonify({"error": "Unauthorized"}), 401

            user = User.query.get(uid)
            if not user:
                return jsonify({"error": "User not found"}), 404

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
# BOOKING: CREATE
# =========================================================
@app.route("/bookings", methods=["POST"])
@require_role("hunter")
def create_booking():
    data = request.get_json() or {}

    listing_id = data.get("listingId")
    preferred_slots = data.get("preferredSlots", [])

    hunter = request.current_user

    if not listing_id:
        return jsonify({"error": "listingId is required"}), 400

    listing = Listing.query.get(listing_id)
    if not listing:
        return jsonify({"error": "Listing not found"}), 404

    # Restrict hunter to max 3 bookings in last 72 hours
    cutoff = datetime.utcnow() - timedelta(hours=72)
    count = Booking.query.filter(
        Booking.hunter_id == hunter.id,
        Booking.created_at > cutoff
    ).count()

    if count >= 3:
        return jsonify({"error": "Max 3 bookings within 72 hours"}), 403

    booking = Booking(
        hunter_id=hunter.id,
        listing_id=listing_id,
        preferred_slots=json.dumps(preferred_slots),
        status="pending",
        expires_at=datetime.utcnow() + timedelta(hours=72),
    )

    db.session.add(booking)
    db.session.commit()

    # Notify leaser
    send_fcm_to_user(listing.owner_id, "New Booking", "A hunter requested a booking.")

    return jsonify({"bookingId": booking.id}), 201


# =========================================================
# BOOKING: APPROVE
# =========================================================
@app.route("/bookings/<int:booking_id>/approve", methods=["POST"])
@require_role("leaser")
def approve_booking(booking_id):
    leaser = request.current_user
    data = request.get_json() or {}
    scheduled_slot = data.get("scheduledSlot")

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if booking.listing.owner_id != leaser.id:
        return jsonify({"error": "You cannot approve this booking"}), 403

    booking.status = "confirmed"
    booking.leaser_id = leaser.id
    booking.scheduled_slot = scheduled_slot

    db.session.commit()

    send_fcm_to_user(booking.hunter_id, "Booking Confirmed", "Your booking has been confirmed.")

    return jsonify({"ok": True})


# =========================================================
# BOOKING: GENERATE ONE-TIME CODE
# =========================================================
@app.route("/bookings/<int:booking_id>/generate_code", methods=["POST"])
@require_role("hunter")
def generate_code(booking_id):
    hunter = request.current_user
    booking = Booking.query.get(booking_id)

    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if booking.hunter_id != hunter.id:
        return jsonify({"error": "This is not your booking"}), 403

    code = str(random.randint(100000, 999999))

    booking.one_time_code = code
    booking.code_generated_at = datetime.utcnow()

    db.session.commit()

    send_fcm_to_user(booking.listing.owner_id, "Visitor Code", f"Code: {code}")
    send_fcm_to_user(hunter.id, "Your Code", code)

    return jsonify({"code": code})


# =========================================================
# BOOKING: VERIFY CODE
# =========================================================
@app.route("/bookings/<int:booking_id>/verify_code", methods=["POST"])
@require_role("leaser")
def verify_code(booking_id):
    leaser = request.current_user
    data = request.get_json() or {}
    code = data.get("code")

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if booking.listing.owner_id != leaser.id:
        return jsonify({"error": "Not authorized"}), 403

    if booking.one_time_code != code:
        return jsonify({"error": "Invalid code"}), 403

    booking.status = "booked"
    booking.viewed = True
    booking.viewed_at = datetime.utcnow()

    # Reward leaser
    earnings = Earnings.query.filter_by(leaser_id=leaser.id).first()
    if not earnings:
        earnings = Earnings(leaser_id=leaser.id, balance=100.0)
        db.session.add(earnings)
    else:
        earnings.balance += 100.0

    db.session.commit()

    send_fcm_to_user(booking.hunter_id, "Viewing Complete", "Leaser verified your code.")

    return jsonify({"ok": True})


# =========================================================
# WEBHOOKS: STRIPE
# =========================================================
@app.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    logger.info("Stripe webhook received")
    event = request.get_json()
    logger.info(event)
    return jsonify({"received": True})


# =========================================================
# WEBHOOKS: M-PESA
# =========================================================
@app.route("/webhook/mpesa", methods=["POST"])
def mpesa_webhook():
    logger.info("M-Pesa callback received:")
    logger.info(request.get_json())
    return "OK", 200


# =========================================================
# ADMIN PAYOUT (manual)
# =========================================================
@app.route("/admin/payouts/<int:leaser_id>", methods=["POST"])
def admin_create_payout(leaser_id):
    data = request.get_json() or {}
    amount = float(data.get("amount", 0))

    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    p = Payout(leaser_id=leaser_id, amount=amount)
    db.session.add(p)
    db.session.commit()

    return jsonify({"payoutId": p.id})


# =========================================================
# CRON: MIDNIGHT AUDIT
# =========================================================
def midnight_audit():
    logger.info("Running midnight audit...")

    tomorrow = (datetime.utcnow() + timedelta(days=1)).date()

    bookings = Booking.query.filter_by(status="confirmed").all()

    for b in bookings:
        if b.scheduled_slot and str(tomorrow) in b.scheduled_slot:
            send_fcm_to_user(b.hunter_id, "Viewing Reminder", "You have a viewing tomorrow.")
            send_fcm_to_user(b.listing.owner_id, "Viewing Reminder", "You have a viewing tomorrow.")


# =========================================================
# CRON: WEEKLY PAYOUTS
# =========================================================
def weekly_payouts():
    logger.info("Running weekly payouts...")

    earnings = Earnings.query.filter(Earnings.balance > 0).all()

    for e in earnings:
        payout = Payout(leaser_id=e.leaser_id, amount=e.balance)
        db.session.add(payout)

        e.balance = 0.0  # reset

    db.session.commit()


# =========================================================
# SCHEDULER SETUP
# =========================================================
scheduler = BackgroundScheduler(timezone=TIMEZONE)
scheduler.add_job(midnight_audit, CronTrigger(hour=0, minute=0))
scheduler.add_job(weekly_payouts, CronTrigger(day_of_week="sun", hour=3, minute=0))
scheduler.start()


# =========================================================
# CLI: INIT DB
# =========================================================
@app.cli.command("init-db")
def init_db():
    """Initialize all tables & create default roles."""
    db.create_all()

    for role_name in ("hunter", "leaser", "admin"):
        if not Role.get_by_name(role_name):
            Role.create(role_name)

    # Create admin user
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
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
