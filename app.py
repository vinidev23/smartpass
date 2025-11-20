from flask import Flask, request, jsonify, render_template, redirect, url_for
from models import init_db, SessionLocal, User
from auth import hash_password, verify_password, create_token, decode_token
from datetime import datetime
import uuid
import qrcode
import os

app = Flask(__name__)
init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        
        # Gerar id único para o usuário
        unique_id = str(uuid.uuid4())
        
        # Gera o QR Code após o registro do usuário
        img = qrcode.make(unique_id)
        qr_folder = os.path.join("static", "qrcodes")
        os.makedirs(qr_folder, exist_ok=True)
        
        qr_filename = f"{unique_id}.png"
        qr_path = os.path.join(qr_folder, qr_filename)
        img.save(qr_path)
        
        # Salvar no banco de dados
        
        db = SessionLocal()
        new_user = User(
            name = name,
            email = email,
            unique_id = unique_id,
            qr_code_path = f"qrcodes/{qr_filename}"
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