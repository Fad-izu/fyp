from flask import Blueprint, request, jsonify
from models import db, DetectionLog, Student
import time
import sqlite3
from datetime import datetime, timedelta

api = Blueprint('api', __name__)

@api.route('/api/log_detection', methods=['POST'])
def log_detection():
    try:
        data = request.get_json()
        plate = data.get('plate_number', '').upper().strip()

        if not plate:
            return jsonify({"error": "Missing plate"}), 400

        # Check student record
        student = Student.query.filter_by(plate_number=plate).first()
        status = "GRANTED" if student else "DENIED"

        # Cooldown: skip if same plate within 10s
        last_log = DetectionLog.query.filter_by(plate_number=plate)\
            .order_by(DetectionLog.timestamp.desc())\
            .first()
        if last_log and (datetime.utcnow() - last_log.timestamp) < timedelta(seconds=10):
            print(f"⚠️ Skipped duplicate log for {plate} (within 10 seconds).")
            return jsonify({
                "plate": plate,
                "status": status,
                "student": {
                    "name": student.name if student else None,
                    "matrix_no": student.matrix_no if student else None
                }
            }), 200

        # Retry for locked database writes
        for attempt in range(5):
            try:
                log = DetectionLog(plate_number=plate, status=status)
                db.session.add(log)
                db.session.commit()
                db.session.close()

                print(f"📘 Detection logged: {plate} - {status} ({'Existing student' if student else 'Unknown'})")

                return jsonify({
                    "plate": plate,
                    "status": status,
                    "student": {
                        "name": student.name if student else None,
                        "matrix_no": student.matrix_no if student else None
                    }
                }), 200

            except sqlite3.OperationalError as e:
                if "locked" in str(e):
                    db.session.rollback()
                    print(f"⚠️ Database locked, retrying... ({attempt+1}/5)")
                    time.sleep(0.2)
                    continue
                raise

        return jsonify({"error": "Database busy, please retry"}), 500

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in /api/log_detection: {e}")
        return jsonify({"error": str(e)}), 500


@api.route('/api/logs', methods=['GET'])
def get_logs():
    """Return recent 200 detection logs as JSON"""
    try:
        logs = DetectionLog.query.order_by(DetectionLog.timestamp.desc()).limit(200).all()
        return jsonify([
            {
                "plate_number": l.plate_number,
                "status": l.status,
                "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }
            for l in logs
        ])
    except Exception as e:
        print(f"❌ Error in /api/logs: {e}")
        return jsonify({"error": str(e)}), 500

# ==========================================================
# 🔹 Route: Delete All Logs
# ==========================================================
@api.route('/api/clear_logs', methods=['DELETE'])
def clear_logs():
    """Delete all detection logs"""
    try:
        num_deleted = DetectionLog.query.delete()
        db.session.commit()
        print(f"🧹 Cleared {num_deleted} logs from database.")
        return jsonify({"message": f"Deleted {num_deleted} logs."}), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error clearing logs: {e}")
        return jsonify({"error": str(e)}), 500
