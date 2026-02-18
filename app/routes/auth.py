from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from app import db
from app.models.user import User, Student, Teacher

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password', 'user_type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    try:
        user_type = data['user_type'].lower()
        
        if user_type == 'student':
            user = Student(
                username=data['username'],
                email=data['email'],
                age=data.get('age'),
                education_level=data.get('education_level'),
                major_field=data.get('major_field'),
                english_proficiency_level=data.get('english_proficiency_level'),
                target_exams=data.get('target_exams'),
                location=data.get('location'),
                teacher_id=data.get('teacher_id')
            )
        elif user_type == 'teacher':
            user = Teacher(
                username=data['username'],
                email=data['email'],
                institution_name=data.get('institution_name'),
                education_levels=data.get('education_levels'),
                specialization=data.get('specialization')
            )
        else:
            return jsonify({'error': 'Invalid user type'}), 400
        
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user.id,
            'user_type': user.user_type
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']):
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'user_type': user.user_type,
                'username': user.username
            }
        )
        
        return jsonify({
            'access_token': access_token,
            'user_id': user.id,
            'user_type': user.user_type,
            'username': user.username
        }), 200
    
    return jsonify({'error': 'Invalid username or password'}), 401

@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    profile_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'user_type': user.user_type,
        'created_at': user.created_at.isoformat()
    }
    
    # Add specific data based on user type
    if isinstance(user, Student):
        profile_data.update({
            'age': user.age,
            'education_level': user.education_level,
            'major_field': user.major_field,
            'english_proficiency_level': user.english_proficiency_level,
            'target_exams': user.target_exams,
            'location': user.location,
            'teacher_id': user.teacher_id
        })
    elif isinstance(user, Teacher):
        profile_data.update({
            'institution_name': user.institution_name,
            'education_levels': user.education_levels,
            'specialization': user.specialization,
            'student_count': user.students.count()
        })
    
    return jsonify(profile_data), 200

@bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    try:
        # Update common fields
        if 'email' in data:
            user.email = data['email']
        
        # Update specific fields based on user type
        if isinstance(user, Student):
            if 'age' in data:
                user.age = data['age']
            if 'education_level' in data:
                user.education_level = data['education_level']
            if 'major_field' in data:
                user.major_field = data['major_field']
            if 'english_proficiency_level' in data:
                user.english_proficiency_level = data['english_proficiency_level']
            if 'target_exams' in data:
                user.target_exams = data['target_exams']
            if 'location' in data:
                user.location = data['location']
        elif isinstance(user, Teacher):
            if 'institution_name' in data:
                user.institution_name = data['institution_name']
            if 'education_levels' in data:
                user.education_levels = data['education_levels']
            if 'specialization' in data:
                user.specialization = data['specialization']
        
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Profile update error: {str(e)}")
        return jsonify({'error': 'Profile update failed'}), 500

@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if not data.get('current_password') or not data.get('new_password'):
        return jsonify({'error': 'Current and new passwords required'}), 400
    
    if not user.check_password(data['current_password']):
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    try:
        user.set_password(data['new_password'])
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password change error: {str(e)}")
        return jsonify({'error': 'Password change failed'}), 500

@bp.route('/students', methods=['GET'])
@jwt_required()
def get_students():
    # For teachers to get their students
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    
    if claims.get('user_type') != 'teacher':
        return jsonify({'error': 'Access denied - teachers only'}), 403
    
    teacher_id = int(get_jwt_identity())
    students = Student.query.filter_by(teacher_id=teacher_id).all()
    
    students_data = []
    for student in students:
        students_data.append({
            'id': student.id,
            'username': student.username,
            'age': student.age,
            'education_level': student.education_level,
            'english_proficiency_level': student.english_proficiency_level,
            'created_at': student.created_at.isoformat()
        })
    
    return jsonify({'students': students_data}), 200