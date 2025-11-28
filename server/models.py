from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

# ============================================================
# ROLE
# ============================================================
class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    @classmethod
    def get_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    @classmethod
    def create(cls, name):
        r = cls(name=name)
        db.session.add(r)
        db.session.commit()
        return r


# ============================================================
# USER (HUNTER / LEASER / ADMIN)
# ============================================================
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    _password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    role = db.relationship("Role", backref=db.backref("users", lazy=True))

    # ---- Helpers ----
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self._password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self._password_hash, password)

    def as_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.name,
            "created_at": self.created_at.isoformat(),
        }


# ============================================================
# LISTING (PROPERTY)
# ============================================================
class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    rent = db.Column(db.Float)
    short_description = db.Column(db.Text)
    public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship("User", backref=db.backref("listings", lazy=True))

    def as_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "title": self.title,
            "rent": self.rent,
            "short_description": self.short_description,
            "public": self.public,
            "created_at": self.created_at.isoformat(),
        }


# ============================================================
# BOOKING
# ============================================================
class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    hunter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=False)
    leaser_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    preferred_slots = db.Column(db.Text)  # store JSON list
    status = db.Column(db.String(50), default="pending")  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    scheduled_slot = db.Column(db.String(255), nullable=True)

    one_time_code = db.Column(db.String(16), nullable=True)
    code_generated_at = db.Column(db.DateTime, nullable=True)

    viewed = db.Column(db.Boolean, default=False)
    viewed_at = db.Column(db.DateTime, nullable=True)

    hunter = db.relationship("User", foreign_keys=[hunter_id])
    leaser = db.relationship("User", foreign_keys=[leaser_id])
    listing = db.relationship("Listing")

    def as_dict(self):
        return {
            "id": self.id,
            "hunter_id": self.hunter_id,
            "listing_id": self.listing_id,
            "leaser_id": self.leaser_id,
            "preferred_slots": json.loads(self.preferred_slots) if self.preferred_slots else [],
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scheduled_slot": self.scheduled_slot,
            "viewed": self.viewed,
            "viewed_at": self.viewed_at.isoformat() if self.viewed_at else None,
        }


# ============================================================
# EARNINGS (LEASER REWARD BALANCE)
# ============================================================
class Earnings(db.Model):
    __tablename__ = "earnings"

    id = db.Column(db.Integer, primary_key=True)
    leaser_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True)
    balance = db.Column(db.Float, default=0.0)

    leaser = db.relationship("User", backref=db.backref("earnings", uselist=False))


# ============================================================
# PAYOUT QUEUE (WEEKLY)
# ============================================================
class Payout(db.Model):
    __tablename__ = "payouts"

    id = db.Column(db.Integer, primary_key=True)
    leaser_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# PAYMENT (M-PESA / STRIPE)
# ============================================================
class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="PENDING")
    mpesa_receipt_number = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# PAYMENT LOG (M-PESA CALLBACK LOG)
# ============================================================
class PaymentLog(db.Model):
    __tablename__ = "payment_logs"

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="initiated")
    receipt_number = db.Column(db.String(100))
    merchant_request_id = db.Column(db.String(100))
    checkout_request_id = db.Column(db.String(100))
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============================================================
# FCM DEVICE TOKENS
# ============================================================
class FcmToken(db.Model):
    __tablename__ = "fcm_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    token = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
