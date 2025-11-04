from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Create all database tables
    db.create_all()

    # Enable WAL (Write-Ahead Logging) for better concurrency
    try:
        db.session.execute(text("PRAGMA journal_mode=WAL;"))
        db.session.commit()
        print("✅ SQLite in WAL mode — improved performance and no lock errors.")
    except Exception as e:
        print(f"⚠️ Could not enable WAL mode: {e}")

    # Create default admin account
    from auth import create_admin
    create_admin('admin', 'admin123')

    print("✅ Database initialized and admin user created.")
