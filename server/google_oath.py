# google_oauth.py — Maskani Version (correct!)

import os
from flask import Blueprint, request, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests
from models import db, User, Role
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_cors import cross_origin

google_oauth_bp = Blueprint("google_oauth", __name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


@google_oauth_bp.route("/auth/google", methods=["POST"])
@cross_origin(supports_credentials=True)
def google_auth():
    """Authenticate user via Google OAuth2"""

    token = request.json.get("credential")

    if not token:
        return jsonify({"msg": "Missing credential token"}), 400

    try:
        # 1️⃣ Verify Google token
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        email = idinfo.get("email")
        first_name = idinfo.get("given_name", "")
        last_name = idinfo.get("family_name", "")
        picture = idinfo.get("picture", "")
        google_id = idinfo.get("sub")  # Google unique ID

        if not email:
            return jsonify({"msg": "Google account email not found"}), 400

        # 2️⃣ Get existing user OR create new one
        user = User.query.filter_by(email=email).first()

        if not user:
            # Default Google sign-ups = hunters
            default_role = Role.query.filter_by(name="hunter").first()

            # Generate username safely
            base_username = (first_name + last_name).lower()
            base_username = base_username or ("user" + google_id[-4:])

            # Ensure username is unique
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1

            # Create user
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                profile_pic=picture,
                role_id=default_role.id
            )

            # Google users don't have passwords; store a placeholder hash
            user.set_password(google_id)

            db.session.add(user)
            db.session.commit()

        # 3️⃣ Generate access & refresh tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        # 4️⃣ Return Maskani-formatted response
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile_pic": user.profile_pic,
                "role": user.role.name
            }
        }), 200

    except ValueError:
        return jsonify({"msg": "Invalid Google token"}), 401

    except Exception as e:
        return jsonify({"msg": "Authentication failed", "error": str(e)}), 500
