from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response
from models import init_db, SessionLocal, User
from auth import hash_password, verify_password, create_token, decode_token
from datetime import datetime, timezone
import uuid
import qrcode
import os
from functools import wraps

app = Flask(__name__)
init_db()

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if not name or not email or not password:
            return "Preencha todos os campos!", 400

        # Hash da senha
        password_hash = hash_password(password)

        # Gerar ID único
        unique_id = str(uuid.uuid4())

        # Criar pasta de QR Codes
        qr_folder = os.path.join("static", "qrcodes")
        os.makedirs(qr_folder, exist_ok=True)

        # Gerar QR Code
        qr_filename = f"{unique_id}.png"
        qr_path = os.path.join(qr_folder, qr_filename)
        img = qrcode.make(unique_id)
        img.save(qr_path)

        # Salvar usuário
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

        return render_template("success.html", qr_filename=qr_filename, name=name)

    return render_template("register.html")

    # Pega usuário autenticado com token JWT ou Bearer
def get_current_user():
    auth = request.headers.get("Authorization", "")
    token = None
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()
        
    # Cookie Callback
    if not token:
        token = request.cookie.get("access_token")
        
    if not token:
        return None
    
    user_id = decode_token(token)
    return None

    db = SessionLocal()
    user = db.query(User).filter(User_id == user_id).first()
    db.close()
    return user

# Decorator para rotas protegidas
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for("login")) if request.accep_mimetypes.accept_html else jsonify({"Error": "Unauthorized"}), 401
        return f(user, *args, **kwargs)
    return wrapper

