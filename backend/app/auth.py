# backend/app/auth.py
from flask import Blueprint, request, jsonify
from . import db
from .models import User
from flask_jwt_extended import create_access_token
import bcrypt

# Tạo một Blueprint tên là 'auth'
auth_bp = Blueprint('auth', __name__)

# --- API ĐĂNG KÝ ---
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 1. Validate dữ liệu đầu vào
    if not data or not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({"msg": "Missing fields"}), 400

    # 2. Kiểm tra user đã tồn tại chưa
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"msg": "Email already exists"}), 400
    
    if User.query.filter_by(name=data['name']).first():
        return jsonify({"msg": "Username already exists"}), 400

    # 3. Mã hóa mật khẩu (Hashing)
    # bcrypt.hashpw trả về bytes, cần decode sang utf-8 để lưu vào DB string
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 4. Tạo user mới và lưu vào DB
    new_user = User(
        name=data['name'],
        email=data['email'],
        password_hash=hashed_password
    )
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "User created successfully"}), 201

# --- API ĐĂNG NHẬP ---
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')

    # 1. Tìm user trong DB
    user = User.query.filter_by(email=email).first()

    # 2. Kiểm tra password
    # checkpw(password nhập vào, password trong DB)
    if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        
        # 3. Tạo Token (Vé vào cửa)
        # identity=user.id để sau này biết token này của ai
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            "msg": "Login success",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "name": user.name
            }
        }), 200
    else:
        return jsonify({"msg": "Bad email or password"}), 401