from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response
from models import init_db, SessionLocal, User
from auth import hash_password, verify_password, create_token, decode_token
from datetime import datetime, timedelta, timezone
import uuid
import qrcode
import os
from functools import wraps

app = Flask(__name__)
init_db()

# Obter usuário autenticado
def get_current_user():
    # Bearer token (API)
    auth = request.headers.get("Authorization", "")
    token = None

    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()

    # Cookie (web)
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        return None

    user_id = decode_token(token)
    if not user_id:
        return None

    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()
    return user

# Rota protegida
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.accept_mimetypes.accept_html:
                return redirect(url_for("login"))
            return jsonify({"error": "Unauthorized"}), 401

        return f(user, *args, **kwargs)
    return wrapper


# ROTA DE REGISTRO
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

        # Criar QR Code
        qr_folder = os.path.join("static", "qrcodes")
        os.makedirs(qr_folder, exist_ok=True)

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

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    # POST -> via JSON (API)
    if request.content_type and "application/json" in request.content_type:
        data = request.json or {}
        email = data.get("email")
        password = data.get("password")
    else:
        # POST -> via Form (HTML)
        email = request.form.get("email")
        password = request.form.get("password")

    if not email or not password:
        return jsonify({"error": "missing_credentials"}), 400

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    db.close()

    if not user or not verify_password(user.password_hash, password):
        return jsonify({"error": "invalid_credentials"}), 401

    token = create_token(user.id)

    # Caso seja login por FORM HTML, gera cookie
    if not (request.content_type and "application/json" in request.content_type):
        resp = make_response(redirect(url_for("me_page")))
        resp.set_cookie("access_token", token, httponly=True, samesite="Lax")
        return resp

    # Caso seja API JSON
    return jsonify({"token": token})

# API - Dados do usuário autenticado
@app.route("/api/me", methods=["GET"])
def me_api():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "unique_id": user.unique_id,
        "qr_code_path": user.qr_code_path,
        "last_checkin": user.last_checkin.isoformat() if user.last_checkin else None,
        "created_at": user.created_at.isoformat() if user.created_at else None
    })


# PÁGINA /me/web
@app.route("/me")
@login_required
def me_page(current_user):
    return render_template("me.html", user=current_user)

# DASHBOARD WEB
@app.route("/dashboard")
@login_required
def dashboard(user):
    return render_template("dashboard.html", user=user)

@app.route("/api/checkin", methods=["POST"])
@login_required
def checkin(current_user):
    data = request.json
    if not data or "unique_id" not in data:
        return jsonify({"error:" "unique_id_required"}), 400
    
    unique_id = data["unique_id"]
    
    db = SessionLocal()
    scanned_user = db.query(User).filter(User.unique_id == unique_id).first()
    
    if not scanned_user:
        db.close()
        return jsonify({"error:" "user_not_found"}), 404
    
    # Atualiza o check-in
    scanned_user.last_checkin = datetime.utcnow()
    db.commit()
    db.close()
    
    return jsonify({
        "name": scanned_user.name,
        "email": scanned_user.email,
        "unique_id": scanned_user.unique_id,
        "qr_code_path": scanned_user.qr_code_path,
        "last_checkin": scanned_user.last_checkin.isoformat(),
        "status": "Acesso Autorizado"
    })
    
    db.close()
    return jsonify(response)

@app.route("/api/checkin/<uid>", methods=["GET"])
def api_checkin(uid):
    db = SessionLocal()
    user = db.query(User).filter(User.unique_id == uid).first()
    
    if not user:
        db.close()
        return jsonify({"error": "Usuário não encontrado"}), 400
    
    # Registrar no log
    log = CheckLog(user_id=user.id, action="IN")
    db.add(log)
    
    # Atualizar último check-in
    user.last_checkin = datetime.utcnow()
    
    db.commit()
    db.close()
    
    return jsonify({
        "status": "success",
        "message": f"Check-in efetuado para {user.name}",
        "user": {
            "id": user.id,
            "name": user.name,
            "unique_id": user.unique_id,
        }
    })

# INICIAR SERVIDOR
if __name__ == "__main__":
    app.run(debug=True)
