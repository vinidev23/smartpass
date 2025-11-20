from flask import Flask, request, jsonify, render_template, redirect, url_for
from models import init_db, SessionLocal, User
from auth import hash_password, verify_password, create_token, decode_token
from datetime import datetime
import uuid
import qrcode
import os

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

        
@app.route("/login", methods=["GET", "POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(user.password_hash, password):
        db.close()
        return jsonify({"error": "Credenciais inválidas"}), 401
    token = create_token(user.id)
    db.close()
    return jsonify({"token": token})

if __name__ == "__main__":
    app.run(debug=True)