from flask import Flask, jsonify, request,url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import secrets

from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_mail import Mail,Message

app = Flask(__name__)
CORS(app)
app.secret_key = 'SECRET_KEY'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:pakistan@localhost/Zeenat'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'muneebabbasi079@gmail.com'
app.config['MAIL_PASSWORD'] = 'wglr xweq jruz fdmt'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True



db = SQLAlchemy(app)
mail = Mail(app)
jwt = JWTManager(app)

# User model
class User(db.Model):
    id = db.Column(db.String(255), primary_key=True)  # Use UUID as primary key
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    reset_token = db.Column(db.String(255), nullable=True)

# Signup endpoint
@app.route('/user/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')

    # Check if email is already taken
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400

    # Hash the password before saving it
    hashed_password = generate_password_hash(password)

    # Create and save the user with a dynamically generated UUID
    new_user = User(id=str(uuid.uuid4()), email=email, password=hashed_password, name=name)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

# Login endpoint
@app.route('/user/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    # Find the user by email
    user = User.query.filter_by(email=email).first()

    # Check if user exists and password is correct
    if user and check_password_hash(user.password, password):
        # Create access token
        accessToken = create_access_token(identity=user.id)
        return jsonify({'accessToken': accessToken, 'user': {'id': user.id, 'email': user.email, 'name': user.name}}), 200
        
    else:
        app.logger.error(f'Login failed for email: {email}')
        return jsonify({'error': 'Invalid email or password'}), 401
        
    
    
    
    
@app.route('/user/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    db.session.commit()

    # Send reset password email
    msg = Message('Reset Password Request', sender='zaynababbasy29@gmail.com', recipients=[email])
    reset_link = f"http://localhost:3000/forget-password/{reset_token}"  
    msg.body = f'Please click the following link to reset your password: {reset_link}'
    mail.send(msg)

    return jsonify({'message': 'Reset password email sent'}), 200


    
    
# Confirm forgot password endpoint
@app.route('/user/confirm-forgot-password', methods=['POST'])
def confirm_forgot_password():
    data = request.json
    token = data.get('token')
    new_password = data.get('password')

    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return jsonify({'error': 'Invalid token'}), 400

    # Check if the provided new password is valid
    if not new_password or len(new_password) < 6:
        return jsonify({'error': 'New password is invalid'}), 400

    # Hash the new password
    hashed_password = generate_password_hash(new_password)
    user.password = hashed_password
    user.reset_token = None
    db.session.commit()
    app.logger.info('Password reset successfully')

    return jsonify({'message': 'Password reset successfully'}), 200

# Reset password endpoint
@app.route('/user/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    token = data.get('token')
    new_password = data.get('newPassword')

    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return jsonify({'error': 'Invalid token'}), 400

    # Hash the new password
    hashed_password = generate_password_hash(new_password)
    user.password = hashed_password
    user.reset_token = None
    db.session.commit()
    app.logger.info('Password reset successfully')

    return jsonify({'message': 'Password reset successfully'}), 200

    
@app.route('/')
def index():
    return 'hello world'

if __name__ == '__main__':
     app.run(debug=True)
