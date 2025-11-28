from app import app, db
from models import (
    User, Role, Listing, Booking, Earnings, Payout, FcmToken
)
from datetime import datetime, timedelta

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()

    print("Creating all tables...")
    db.create_all()

    # ---------------------------------------------------
    # SEED ROLES
    # ---------------------------------------------------
    print("Seeding roles...")

    hunter_role = Role.create("hunter")
    leaser_role = Role.create("leaser")
    admin_role = Role.create("admin")  # Role exists but no user uses it yet

    db.session.commit()
    print("Roles seeded.")

    # ---------------------------------------------------
    # SEED USERS (NO ADMIN CREATED)
    # ---------------------------------------------------
    print("Seeding users...")

    # Hunters
    hunter1 = User(username="hunter_jane", email="jane@maskani.com", role_id=hunter_role.id)
    hunter1.set_password("password123")

    hunter2 = User(username="hunter_mike", email="mike@maskani.com", role_id=hunter_role.id)
    hunter2.set_password("password123")

    # Leasers
    leaser1 = User(username="leaser_anna", email="anna@maskani.com", role_id=leaser_role.id)
    leaser1.set_password("leaserpass")

    leaser2 = User(username="leaser_mark", email="mark@maskani.com", role_id=leaser_role.id)
    leaser2.set_password("leaserpass")

    db.session.add_all([hunter1, hunter2, leaser1, leaser2])
    db.session.commit()
    print("Users seeded.")

    # ---------------------------------------------------
    # SEED LISTINGS
    # ---------------------------------------------------
    print("Seeding listings...")

    listing1 = Listing(
        owner_id=leaser1.id,
        title="2 Bedroom Apartment in Kilimani",
        rent=45000,
        short_description="Modern 2 bedroom apartment with balcony and parking.",
        public=True
    )

    listing2 = Listing(
        owner_id=leaser2.id,
        title="Bedsitter in Rongai",
        rent=12000,
        short_description="Affordable single room with running water.",
        public=True
    )

    listing3 = Listing(
        owner_id=leaser2.id,
        title="1 Bedroom in Westlands",
        rent=35000,
        short_description="Cozy 1 bedroom close to malls and restaurants.",
        public=True
    )

    db.session.add_all([listing1, listing2, listing3])
    db.session.commit()
    print("Listings seeded.")

    # ---------------------------------------------------
    # SEED BOOKINGS
    # ---------------------------------------------------
    print("Seeding bookings...")

    booking1 = Booking(
        hunter_id=hunter1.id,
        listing_id=listing1.id,
        preferred_slots='["2025-03-02 10:00", "2025-03-02 15:00"]',
        status="confirmed",
        scheduled_slot="2025-03-02 10:00",
        expires_at=datetime.utcnow() + timedelta(hours=72),
        leaser_id=leaser1.id
    )

    booking2 = Booking(
        hunter_id=hunter2.id,
        listing_id=listing2.id,
        preferred_slots='["2025-03-05 12:00"]',
        status="pending",
        expires_at=datetime.utcnow() + timedelta(hours=72)
    )

    db.session.add_all([booking1, booking2])
    db.session.commit()
    print("Bookings seeded.")

    # ---------------------------------------------------
    # SEED EARNINGS
    # ---------------------------------------------------
    print("Seeding earnings...")

    earnings1 = Earnings(leaser_id=leaser1.id, balance=200.0)
    earnings2 = Earnings(leaser_id=leaser2.id, balance=100.0)

    db.session.add_all([earnings1, earnings2])
    db.session.commit()
    print("Earnings seeded.")

    # ---------------------------------------------------
    # SEED PAYOUTS
    # ---------------------------------------------------
    print("Seeding payout queue...")

    payout1 = Payout(
        leaser_id=leaser1.id,
        amount=200.0,
        status="pending"
    )

    db.session.add(payout1)
    db.session.commit()
    print("Payout seeded.")

    # ---------------------------------------------------
    # SEED FCM TOKENS
    # ---------------------------------------------------
    print("Seeding FCM tokens...")

    token1 = FcmToken(user_id=leaser1.id, token="fcm_token_anna")
    token2 = FcmToken(user_id=hunter1.id, token="fcm_token_jane")

    db.session.add_all([token1, token2])
    db.session.commit()
    print("FCM tokens seeded.")

    print("Database seeding complete!")
