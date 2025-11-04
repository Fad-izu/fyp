from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, Response, session
from models import db, Admin, Student, DetectionLog
from auth import create_admin, verify_admin
from api import api
import cv2

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smart_parking.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'replace-with-secure-key'
    db.init_app(app)
    app.register_blueprint(api)

    # ✅ Initialize database
    with app.app_context():
        db.create_all()
        create_admin('admin', 'admin123')

    # ==============================
    # 🏠 HOMEPAGE
    # ==============================
    @app.route('/')
    @app.route('/index')
    def home():
        return render_template('index.html')

    # ==============================
    # 👨‍💼 ADMIN LOGIN
    # ==============================
    @app.route('/admin_login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            u = request.form.get('username')
            p = request.form.get('password')
            if verify_admin(u, p):
                session['admin'] = u
                return redirect(url_for('dashboard'))
            flash('Invalid credentials', 'danger')
        return render_template('login.html')

    @app.route('/dashboard')
    def dashboard():
        if not is_logged_in():
            return redirect(url_for('admin_login'))
        total_students = Student.query.count()
        total_logs = DetectionLog.query.count()
        return render_template('dashboard.html', total_students=total_students, total_logs=total_logs)

    # ==============================
    # 👩‍🎓 STUDENT PORTAL
    # ==============================
    @app.route('/student_portal', methods=['GET', 'POST'])
    def student_portal():
        """
        Main student access page:
        - GET: Show form
        - POST: Check plate number
        """
        if request.method == 'POST':
            plate = request.form.get('plate_number', '').upper().strip()
            if not plate:
                flash("Please enter your plate number!", "warning")
                return redirect(url_for('student_portal'))

            student = Student.query.filter_by(plate_number=plate).first()
            if student:
                return render_template('student_portal.html', student=student)
            else:
                return render_template('student_not_found.html', plate=plate)

        return render_template('student_portal.html', student=None)

    # ==============================
    # 👨‍🎓 STUDENT MANAGEMENT
    # ==============================
    @app.route('/students')
    def students_page():
        if not is_logged_in():
            return redirect(url_for('admin_login'))
        students = Student.query.all()
        return render_template('students.html', students=students)

    @app.route('/add_student', methods=['GET', 'POST'])
    def add_student():
        if not is_logged_in():
            return redirect(url_for('admin_login'))
        if request.method == 'POST':
            plate = request.form.get('plate', '').upper().strip()
            name = request.form.get('name', '')
            matrix = request.form.get('matrix', '')
            if not plate or not name:
                flash('Plate and name required', 'warning')
                return render_template('add_student.html')
            s = Student(plate_number=plate, name=name, matrix_no=matrix)
            db.session.add(s)
            db.session.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('students_page'))
        return render_template('add_student.html')

    @app.route('/delete_student/<int:id>', methods=['POST'])
    def delete_student(id):
        if not is_logged_in():
            return redirect(url_for('admin_login'))
        student = Student.query.get_or_404(id)
        db.session.delete(student)
        db.session.commit()
        flash(f'Student {student.name} deleted successfully!', 'success')
        return redirect(url_for('students_page'))

    # ==============================
    # 🧾 LOGS
    # ==============================
    @app.route('/logs')
    def logs():
        if not is_logged_in():
            return redirect(url_for('admin_login'))
        logs = DetectionLog.query.order_by(DetectionLog.timestamp.desc()).limit(200).all()
        return render_template('logs.html', logs=logs)

    # ==============================
    # 🎥 CAMERA STREAM
    # ==============================
    def generate_frames():
        cap = cv2.VideoCapture(0)
        while True:
            success, frame = cap.read()
            if not success:
                break
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    @app.route('/camera')
    def camera_page():
        return render_template('camera.html')

    @app.route('/video_feed')
    def video_feed():
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    # ==============================
    # 🔐 SESSION HELPERS
    # ==============================
    def is_logged_in():
        return bool(session.get('admin'))

    @app.route('/logout')
    def logout():
        session.pop('admin', None)
        return redirect(url_for('admin_login'))

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
