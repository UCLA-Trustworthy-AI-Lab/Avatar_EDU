import os
from app import create_app, db
from app.models.user import User, Student, Teacher
from app.models.reading import ReadingMaterial, ReadingSession, VocabularyInteraction, ReadingProgress
from config import config

app = create_app(config[os.environ.get('FLASK_ENV', 'development')])

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Student': Student,
        'Teacher': Teacher,
        'ReadingMaterial': ReadingMaterial,
        'ReadingSession': ReadingSession,
        'VocabularyInteraction': VocabularyInteraction,
        'ReadingProgress': ReadingProgress
    }

@app.cli.command()
def create_tables():
    """Create database tables."""
    db.create_all()
    print("Database tables created.")

@app.cli.command()
def init_db():
    """Initialize database with sample data."""
    db.create_all()
    
    # Create sample student for testing (Chinese high school student)
    if not Student.query.filter_by(username='student1').first():
        student = Student(
            username='student1',
            email='student@example.com',
            age=18,
            education_level='high school',
            major_field='Science',
            english_proficiency_level='intermediate',
            target_exams=['TOEFL', 'IELTS'],
            location='Beijing, China'
        )
        student.set_password('password123')
        db.session.add(student)
        db.session.commit()
        
        print("Sample data created:")
        print("Student - username: student1, password: password123")
        print("Profile: 18 years old, intermediate English, targeting TOEFL/IELTS")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)