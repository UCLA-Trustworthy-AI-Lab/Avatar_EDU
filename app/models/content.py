from datetime import datetime
from app import db

class CustomContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # text, audio, image, video
    module_type = db.Column(db.String(20), nullable=False)  # listening, speaking, reading, writing
    
    # Content storage
    content_text = db.Column(db.Text)
    content_url = db.Column(db.String(500))  # S3 URL for media files
    file_path = db.Column(db.String(500))  # Local/S3 file path
    
    # Metadata
    difficulty_level = db.Column(db.String(20), default='intermediate')
    target_grade = db.Column(db.String(20))
    tags = db.Column(db.JSON)  # Searchable tags
    
    # Usage tracking
    usage_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def increment_usage(self):
        self.usage_count += 1
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content_type': self.content_type,
            'module_type': self.module_type,
            'content_text': self.content_text,
            'content_url': self.content_url,
            'difficulty_level': self.difficulty_level,
            'target_grade': self.target_grade,
            'tags': self.tags,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }