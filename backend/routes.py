from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from models import db, User, Image, Comment
from config import Config

routes = Blueprint('routes', __name__)

# ✅ Serve Uploaded Images
@routes.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)

# ✅ User Registration
@routes.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'consumer')

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 400

    new_user = User(username=username, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'})

# ✅ User Login
@routes.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()

    if not user or user.password != data.get('password'):
        return jsonify({'message': 'Invalid credentials'}), 401

    access_token = create_access_token(identity={'username': user.username, 'role': user.role})
    return jsonify({'access_token': access_token})

# ✅ Image Upload (Only for Creators)
@routes.route('/upload', methods=['POST'])
@jwt_required()
def upload_image():
    user = get_jwt_identity()
    if user['role'] != 'creator':
        return jsonify({'message': 'Only creators can upload images'}), 403

    if 'image' not in request.files:
        return jsonify({'message': 'No image uploaded'}), 400

    image = request.files['image']
    filename = secure_filename(image.filename)
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    image.save(filepath)

    new_image = Image(filename=filename, uploader=user['username'])
    db.session.add(new_image)
    db.session.commit()

    return jsonify({'message': 'Image uploaded successfully'})

# ✅ Fetch All Images (For Feed)
@routes.route('/images', methods=['GET'])
def get_images():
    images = Image.query.all()
    image_list = [
        {
            "id": img.id,
            "filename": img.filename,
            "uploader": img.uploader,
            "url": f"/static/uploads/{img.filename}"  # ✅ Now served by Flask
        }
        for img in images
    ]
    return jsonify(image_list)

# ✅ Delete Image (Only for Creators)
@routes.route('/delete/<int:image_id>', methods=['DELETE'])
@jwt_required()
def delete_image(image_id):
    user = get_jwt_identity()
    image = Image.query.get(image_id)

    if not image:
        return jsonify({'message': 'Image not found'}), 404

    # ✅ Only uploader can delete their image
    if image.uploader != user['username']:
        return jsonify({'message': 'Unauthorized'}), 403

    # ✅ Delete image from server storage
    image_path = os.path.join(Config.UPLOAD_FOLDER, image.filename)
    if os.path.exists(image_path):
        os.remove(image_path)

    # ✅ Delete image from database
    db.session.delete(image)
    db.session.commit()

    return jsonify({'message': 'Image deleted successfully'})

# ✅ Add Comment to Image
@routes.route('/comment', methods=['POST'])
@jwt_required()
def add_comment():
    user = get_jwt_identity()
    data = request.json
    image_id = data.get("image_id")
    text = data.get("text")

    if not text or not image_id:
        return jsonify({"message": "Missing data"}), 400

    new_comment = Comment(image_id=image_id, commenter=user['username'], text=text)  # ✅ Fixed `username` to `commenter`
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({"message": "Comment added successfully"})

# ✅ Get Comments for an Image
@routes.route('/comments/<int:image_id>', methods=['GET'])
def get_comments(image_id):
    comments = Comment.query.filter_by(image_id=image_id).all()
    comment_list = [
        {
            "id": c.id,
            "username": c.commenter,  # ✅ Fixed: Use `commenter` instead of `username`
            "text": c.text
        }
        for c in comments
    ]
    return jsonify(comment_list)
