from flask import (
    Flask, request, jsonify, render_template,
    redirect, url_for, session
)
from models import init_db, SessionLocal, User, CheckLog
from auth import hash_password, verify_password
from datetime import datetime
import uuid
import qrcode
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = "smartpass-secret-key"

init_db()

def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None

    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()
    return user


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for("login"))
        return f(user, *args, **kwargs)
    return wrapper

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")


        if not name or not email or not password:
            return "Preencha todos os campos!", 400

        password_hash = hash_password(password)
        unique_id = str(uuid.uuid4())

        qr_folder = os.path.join("static", "qrcodes")
        os.makedirs(qr_folder, exist_ok=True)

        qr_filename = f"{unique_id}.png"
        qr_path = os.path.join(qr_folder, qr_filename)
        img = qrcode.make(unique_id)
        img.save(qr_path)

        db = SessionLocal()
        new_user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            unique_id=unique_id,
            qr_code_path=f"qrcodes/{qr_filename}",
            created_at=datetime.utcnow(),
        )
        db.add(new_user)
        db.commit()
        db.close()

        return render_template("success.html", name=name)

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        return render_template("login.html", error="Preencha todos os campos!")

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    db.close()

    if not user or not verify_password(user.password_hash, password):
        return render_template("login.html", error="Email ou senha inválidos!")

    # ✅ LOGIN OK → SESSION
    session["user_id"] = user.id

    return redirect(url_for("me_page"))

@app.route("/me")
@login_required
def me_page(current_user):
    return render_template("me.html", user=current_user)

@app.route("/dashboard")
@login_required
def dashboard(current_user):
    return render_template("dashboard.html", user=current_user)

@app.route("/api/checkin", methods=["POST"])
@login_required
def checkin(current_user):
    data = request.json
    if not data or "unique_id" not in data:
        return jsonify({"error": "unique_id_required"}), 400

    db = SessionLocal()
    scanned_user = db.query(User).filter(
        User.unique_id == data["unique_id"]
    ).first()

    if not scanned_user:
        db.close()
        return jsonify({"error": "user_not_found"}), 404

    scanned_user.last_checkin = datetime.utcnow()
    db.commit()
    db.close()

    return jsonify({
        "status": "Acesso Autorizado",
        "name": scanned_user.name,
        "email": scanned_user.email,
        "unique_id": scanned_user.unique_id,
        "last_checkin": scanned_user.last_checkin.isoformat()
    })

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)