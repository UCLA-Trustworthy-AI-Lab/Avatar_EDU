#!/usr/bin/env python3
"""
Create a demo user for testing the conversation module
"""

import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User, Student
from werkzeug.security import generate_password_hash

def create_demo_user():
    """Create a demo student user for testing"""
    
    # Configuration for different environments
    config = {
        'development': 'config.DevelopmentConfig',
        'testing': 'config.TestingConfig', 
        'production': 'config.ProductionConfig'
    }
    
    # Create app
    app = create_app(config[os.environ.get('FLASK_ENV', 'development')])
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if demo user already exists
        existing_user = User.query.filter_by(username='demo_student').first()
        if existing_user:
            print("Demo user already exists!")
            print(f"Username: demo_student")
            print(f"Password: password123")
            return
        
        # Create demo student user
        demo_user = Student(
            username='demo_student',
            email='demo@example.com',
            password_hash=generate_password_hash('password123'),
            age=20,
            education_level='undergraduate',
            major_field='Computer Science',
            english_proficiency_level='intermediate',
            target_exams=['TOEFL', 'IELTS'],
            location='Beijing, China',
            created_at=datetime.utcnow(),
            is_active=True,
            user_type='student'
        )
        
        # Add to database
        db.session.add(demo_user)
        db.session.commit()
        
        print("✅ Demo user created successfully!")
        print(f"Username: demo_student")
        print(f"Password: password123")
        print(f"User ID: {demo_user.id}")
        print(f"Email: {demo_user.email}")
        print(f"Education Level: {demo_user.education_level}")
        print(f"English Level: {demo_user.english_proficiency_level}")

if __name__ == '__main__':
    create_demo_user()