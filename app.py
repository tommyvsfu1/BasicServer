from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy 
from pymongo import MongoClient 
import os


app = Flask(__name__)

# 1. SQLite 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app) # 必須加上這行
class UserCore(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client['user_system']
mongo_collection = mongo_db['preferences']

with app.app_context():
    db.create_all()


# 2. RESTful API
@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error":"缺少必填欄位 (email or password)"}), 400

    try:
        # step 1
        new_user = UserCore(email=data['email'], password_hash=data['password'])
        db.session.add(new_user)
        db.session.commit()

        # step 2
        prefs = data.get('preferences', {})
        mongo_collection.insert_one({
            "user_id" : new_user.id, 
            "settings" : prefs
        })

        return jsonify({"message":"使用者建立成功!", "user_id":new_user.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error":str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # 從SQLite 抓取核心資料
    user_core = UserCore.query.get(user_id)
    if not user_core:
        return jsonify({"error":"找不到該使用者"}), 404

    # 從MongoDB 抓取偏好
    user_prefs = mongo_collection.find_one({"user_id":user_id}, {"_id":0})
    return jsonify({"id":user_core.id, "email":user_core.email, "preferences":user_prefs.get('settings',{}) if user_prefs else {}
    }), 200

# Update (PUT)
@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_preferences(user_id):
    data = request.json
    new_prefs = data.get('preferences')

    if new_prefs is None:
        return jsonify({"error":"沒有提供更新的preferences"}), 400

    result = mongo_collection.update_one(
        {"user_id": user_id},
        {"$set": {"settings": new_prefs}}
    )

    if result.matched_count == 0:
        return jsonify({"error":"找不到使用者紀錄"}), 404
    
    return jsonify({"message":"偏好設定更新成功!"}), 200

# Delete (DELETE)
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user_core = UserCore.query.get(user_id)
    if not user_core:
        return jsonify({"error":"找不到該使用者"}), 404
    
    db.session.delete(user_core)
    db.session.commit()

    mongo_collection.delete_one({"user_id":user_id})

    return jsonify({"message": f"使用者 ID {user_id} 已徹底刪除"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)