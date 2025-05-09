from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import os
from models import db, User, Image, Comment
from config import Config
from routes import routes

# ✅ Initialize Flask App
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# ✅ Initialize Database & JWT
db.init_app(app)
jwt = JWTManager(app)

# ✅ Register Routes
app.register_blueprint(routes)

# ✅ Ensure Uploads Folder Exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ✅ Register Route
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'consumer')  # Default role: Consumer
    
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 400
    
    new_user = User(username=username, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'})

# ✅ Login Route
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    
    if not user or user.password != data.get('password'):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity={'username': user.username, 'role': user.role})
    return jsonify({'access_token': access_token})

# ✅ Image Upload Route (Only Creators)
@app.route('/upload', methods=['POST'])
@jwt_required()
def upload_image():
    user = get_jwt_identity()
    if user['role'] != 'creator':
        return jsonify({'message': 'Only creators can upload images'}), 403
    
    if 'image' not in request.files:
        return jsonify({'message': 'No image uploaded'}), 400
    
    image = request.files['image']
    filename = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    image.save(filename)
    
    new_image = Image(filename=image.filename, uploader=user['username'])
    db.session.add(new_image)
    db.session.commit()
    
    return jsonify({'message': 'Image uploaded successfully'})

# ✅ Fetch Image Feed
@app.route('/feed', methods=['GET'])
def image_feed():
    images = Image.query.all()
    return jsonify([{'id': img.id, 'filename': img.filename, 'uploader': img.uploader} for img in images])

# ✅ Add Comment Route
@app.route('/comment', methods=['POST'])
@jwt_required()
def add_comment():
    user = get_jwt_identity()
    data = request.json
    image_id = data.get('image_id')
    text = data.get('text')

    if not text or not image_id:
        return jsonify({'message': 'Missing required fields'}), 400
    
    new_comment = Comment(text=text, image_id=image_id, commenter=user['username'])
    db.session.add(new_comment)
    db.session.commit()
    
    return jsonify({'message': 'Comment added'})

# ✅ Delete Image Route (Only Creator)
@app.route('/delete/<int:image_id>', methods=['DELETE'])
@jwt_required()
def delete_image(image_id):
    user = get_jwt_identity()
    image = Image.query.get(image_id)
    
    if not image:
        return jsonify({'message': 'Image not found'}), 404

    if image.uploader != user['username']:
        return jsonify({'message': 'Unauthorized'}), 403

    # 🔥 Delete Related Comments First
    Comment.query.filter_by(image_id=image_id).delete()

    # ✅ Delete Image
    db.session.delete(image)
    db.session.commit()
    
    return jsonify({'message': 'Image deleted successfully'})

# ✅ Run the App
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created
    app.run(debug=True)
