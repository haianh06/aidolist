# backend/app/events.py
from flask import Blueprint, request, jsonify
from . import db
from .models import Event
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

events_bp = Blueprint('events', __name__)

# --- 1. LẤY DANH SÁCH SỰ KIỆN (GET) ---
@events_bp.route('/', methods=['GET'])
@jwt_required()
def get_events():
    # Lấy ID của user đang đăng nhập từ Token
    current_user_id = get_jwt_identity()

    # Lấy tham số filter từ URL
    # Để tránh load cả nghìn sự kiện cũ, Frontend sẽ chỉ xin dữ liệu của tháng đang xem
    start_param = request.args.get('start')
    end_param = request.args.get('end')

    query = Event.query.filter_by(user_id=current_user_id)

    if start_param and end_param:
        # Chuyển string sang datetime để so sánh
        # Lưu ý: Client phải gửi format ISO (VD: 2023-11-24T00:00:00)
        start_date = datetime.fromisoformat(start_param.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end_param.replace('Z', '+00:00'))
        query = query.filter(Event.start_time >= start_date, Event.end_time <= end_date)

    events = query.all()

    # Chuyển object Python thành JSON trả về
    output = []
    for event in events:
        output.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat()
        })

    return jsonify(output), 200

# --- 2. TẠO SỰ KIỆN MỚI (POST) ---
@events_bp.route('/', methods=['POST'])
@jwt_required()
def create_event():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data.get('title') or not data.get('start') or not data.get('end'):
        return jsonify({"msg": "Missing fields"}), 400

    try:
        # Parse thời gian từ string client gửi lên
        start_time = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"msg": "Invalid date format"}), 400

    new_event = Event(
        title=data['title'],
        description=data.get('description', ''),
        start_time=start_time,
        end_time=end_time,
        user_id=current_user_id # Gán sự kiện này cho user đang login
    )

    db.session.add(new_event)
    db.session.commit()

    return jsonify({"msg": "Event created", "id": new_event.id}), 201

# --- 3. XÓA SỰ KIỆN (DELETE) ---
@events_bp.route('/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    current_user_id = get_jwt_identity()
    
    # Tìm sự kiện theo ID
    event = Event.query.get_or_404(event_id)

    # GUARD: Kiểm tra xem user này có phải chủ sở hữu sự kiện không?
    # get_jwt_identity trả về string, user_id trong DB là int, cần ép kiểu để so sánh
    if str(event.user_id) != str(current_user_id): 
        return jsonify({"msg": "Permission denied"}), 403

    db.session.delete(event)
    db.session.commit()

    return jsonify({"msg": "Event deleted"}), 200

# --- 4. CẬP NHẬT SỰ KIỆN (PUT) ---
def update_event(event_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    event = Event.query.get_or_404(event_id)

    if str(event.user_id) != str(current_user_id): 
        return jsonify({"msg": "Permission denied"}), 403

    if not data.get('title') or not data.get('start') or not data.get('end'):
        return jsonify({"msg": "Missing fields"}), 400

    try:
        start_time = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"msg": "Invalid date format"}), 400

    event.title = data['title']
    event.description = data.get('description', '')
    event.start_time = start_time
    event.end_time = end_time

    db.session.commit()

    return jsonify({"msg": "Event updated"}), 200