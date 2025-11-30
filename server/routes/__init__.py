def init_routes(app):
    from .auth import auth_bp
    from .bookings import bookings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(bookings_bp)
