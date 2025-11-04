from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ==========================================================
# 🔹 Admin table
# ==========================================================
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# ==========================================================
# 🔹 Student table
# ==========================================================
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    matrix_no = db.Column(db.String(30), nullable=True)

# ==========================================================
# 🔹 Detection logs table
# ==========================================================
class DetectionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), nullable=False)  # ✅ Must exist!
    status = db.Column(db.String(10), nullable=False)        # GRANTED or DENIED
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
