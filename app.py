from flask import Flask, request, jsonify, render_template, redirect
from models import init_db, SessionLocal, User
from auth import hash_password, verify_pasword, create_token, decode_token
from datetime import datetime

app = Flask(__name__)
init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    db = SessionLocal()
    
    if db.query(User).filter(User.email == email).first():
        db.close()
        return jsonify({"error": "Usuário já cadastrado"}), 400
    
    user = User(name=name, email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit
    db.refresh(user)
    db.close()
    return ({"message": "Usuário criado com sucesso!"})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_pasword(user.password_hash, password):
        db.close()
        return jsonify({"error": "Credenciais inválidas"}), 401
    token = create_token(user.id)
    db.close()
    return jsonify({"token": token})

if __name__ == "__main__":
    app.run(debug=True)