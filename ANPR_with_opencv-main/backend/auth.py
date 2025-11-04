from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Admin

def create_admin(username, password):
    if Admin.query.filter_by(username=username).first(): return
    admin = Admin(username=username, password=generate_password_hash(password))
    db.session.add(admin); db.session.commit()

def verify_admin(username, password):
    a = Admin.query.filter_by(username=username).first()
    if not a: return False
    return check_password_hash(a.password, password)
