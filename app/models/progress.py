from datetime import datetime
from sqlalchemy import func
from app import db

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    module_type = db.Column(db.String(20), nullable=False)  # listening, speaking, reading, writing
    
    # Overall progress metrics
    total_sessions = db.Column(db.Integer, default=0)
    completed_sessions = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, default=0.0)
    
    # Improvement tracking
    improvement_areas = db.Column(db.JSON)  # Areas needing focus
    strengths = db.Column(db.JSON)  # Areas where student excels
    
    # Time tracking
    total_time_minutes = db.Column(db.Integer, default=0)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def completion_percentage(self):
        if self.total_sessions == 0:
            return 0
        return (self.completed_sessions / self.total_sessions) * 100
    
    def update_from_session(self, session):
        self.total_sessions += 1
        if session.is_completed:
            self.completed_sessions += 1
        
        if session.performance_score:
            # Update average score
            if self.average_score == 0:
                self.average_score = session.performance_score
            else:
                total_score = self.average_score * (self.completed_sessions - 1)
                self.average_score = (total_score + session.performance_score) / self.completed_sessions
        
        if session.duration_minutes:
            self.total_time_minutes += session.duration_minutes
        
        self.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'module_type': self.module_type,
            'completion_percentage': self.completion_percentage(),
            'average_score': self.average_score,
            'total_sessions': self.total_sessions,
            'completed_sessions': self.completed_sessions,
            'total_time_minutes': self.total_time_minutes,
            'improvement_areas': self.improvement_areas,
            'strengths': self.strengths,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }

class ModuleProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    module_type = db.Column(db.String(20), nullable=False)
    skill_area = db.Column(db.String(50), nullable=False)  # pronunciation, comprehension, grammar, etc.
    
    current_level = db.Column(db.String(20), default='beginner')  # beginner, intermediate, advanced
    score_history = db.Column(db.JSON)  # Track score progression
    mastery_percentage = db.Column(db.Float, default=0.0)
    
    needs_attention = db.Column(db.Boolean, default=False)
    priority_level = db.Column(db.Integer, default=1)  # 1=low, 5=urgent
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)