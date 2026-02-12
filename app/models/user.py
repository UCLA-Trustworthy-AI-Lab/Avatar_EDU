from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    user_type = db.Column(db.String(20), nullable=False)
    
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': user_type
    }
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Teacher(User):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    institution_name = db.Column(db.String(200))
    subjects_taught = db.Column(db.JSON)  # JSON array of subjects
    education_levels = db.Column(db.String(100))  # high school, undergraduate, graduate
    specialization = db.Column(db.String(100))  # TOEFL prep, academic writing, etc.
    students = db.relationship('Student', backref='teacher', lazy='dynamic', foreign_keys='Student.teacher_id')
    custom_content = db.relationship('CustomContent', backref='teacher', lazy='dynamic')
    
    __mapper_args__ = {
        'polymorphic_identity': 'teacher'
    }

class Student(User):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    age = db.Column(db.Integer)  # 16-20
    education_level = db.Column(db.String(20))  # high school, undergraduate, graduate
    major_field = db.Column(db.String(100))  # Academic major or area of study
    english_proficiency_level = db.Column(db.String(20))  # beginner, intermediate, advanced
    target_exams = db.Column(db.JSON)  # JSON array of target exams (TOEFL, IELTS, GRE, etc.)
    location = db.Column(db.String(100))  # City/region in China mainland
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)  # Optional
    
    sessions = db.relationship('LearningSession', backref='student', lazy='dynamic')
    progress = db.relationship('Progress', backref='student', lazy='dynamic')
    reading_sessions = db.relationship('ReadingSession', backref='student', lazy='dynamic')
    vocabulary_interactions = db.relationship('VocabularyInteraction', backref='student', lazy='dynamic')
    reading_progress = db.relationship('ReadingProgress', backref='student', lazy='dynamic')
    
    __mapper_args__ = {
        'polymorphic_identity': 'student'
    }