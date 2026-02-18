from datetime import datetime
from app import db

class LearningSession(db.Model):
    __tablename__ = 'learning_sessions'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    module_type = db.Column(db.String(20), nullable=False)  # listening, speaking, reading, writing
    activity_type = db.Column(db.String(50))
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)
    is_completed = db.Column(db.Boolean, default=False)
    
    # Session data (JSON fields for flexibility)
    session_data = db.Column(db.JSON)  # Store questions, responses, scores, etc.
    performance_score = db.Column(db.Float)  # Overall session score (0-100)
    
    # Context tracking
    previous_session_id = db.Column(db.Integer, db.ForeignKey('learning_sessions.id'))
    context_data = db.Column(db.JSON)  # Store conversation/learning context
    
    def complete_session(self, score=None, data=None):
        self.completed_at = datetime.utcnow()
        self.is_completed = True
        if score:
            self.performance_score = score
        if data:
            self.session_data = data
        self.duration_minutes = int((self.completed_at - self.started_at).total_seconds() / 60)
    
    def to_dict(self):
        return {
            'id': self.id,
            'module_type': self.module_type,
            'activity_type': self.activity_type,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_minutes': self.duration_minutes,
            'is_completed': self.is_completed,
            'performance_score': self.performance_score,
            'session_data': self.session_data
        }

class ConversationSession(db.Model):
    """Model for storing conversation session data"""
    __tablename__ = 'conversation_session'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)  # HeyGen session ID
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    learning_session_id = db.Column(db.Integer, db.ForeignKey('learning_sessions.id'), nullable=True)
    
    # Session metadata
    conversation_topic = db.Column(db.String(50))  # general, daily_life, academic, business, travel
    platform = db.Column(db.String(20), default='heygen')  # heygen, custom, text
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    
    # Conversation metrics
    total_turns = db.Column(db.Integer, default=0)
    student_words_count = db.Column(db.Integer, default=0)
    avatar_words_count = db.Column(db.Integer, default=0)
    
    # Conversation content
    conversation_transcript = db.Column(db.JSON)  # Full conversation history
    
    # Performance scores (0-100)
    fluency_score = db.Column(db.Float)
    pronunciation_score = db.Column(db.Float)
    logical_flow_score = db.Column(db.Float)
    vocabulary_complexity = db.Column(db.Integer)  # 1-10
    engagement_level = db.Column(db.Integer)  # 0-100
    response_appropriateness = db.Column(db.Float)  # 0-100
    grammar_accuracy = db.Column(db.Float)  # 0-100
    
    # Additional analytics
    conversation_length_seconds = db.Column(db.Integer)
    pause_analysis = db.Column(db.JSON)  # Speech pause data
    topic_adherence = db.Column(db.Float)  # How well stayed on topic (0-100)
    questions_asked = db.Column(db.Integer, default=0)
    complex_responses = db.Column(db.Integer, default=0)
    
    # Learning insights
    future_recommendations = db.Column(db.JSON)  # Array of improvement suggestions
    achievements = db.Column(db.JSON)  # Array of achievements earned
    improvement_areas = db.Column(db.JSON)  # Array of areas needing work
    
    def complete_session(self, analytics_data: dict = None):
        """Complete the conversation session with analytics"""
        self.completed_at = datetime.utcnow()
        self.is_active = False
        self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        
        if analytics_data:
            # Update scores from analytics
            self.fluency_score = analytics_data.get('fluency_score')
            self.pronunciation_score = analytics_data.get('pronunciation_score')
            self.logical_flow_score = analytics_data.get('conversation_flow_score')
            self.vocabulary_complexity = analytics_data.get('vocabulary_complexity_score')
            self.engagement_level = self._calculate_engagement_level(analytics_data)
            self.questions_asked = analytics_data.get('questions_asked', 0)
            self.complex_responses = analytics_data.get('complex_responses', 0)
            self.topic_adherence = analytics_data.get('topic_adherence', 100)
            
            # Store learning insights
            self.future_recommendations = analytics_data.get('recommendations', [])
            self.achievements = analytics_data.get('achievements', [])
            self.improvement_areas = analytics_data.get('improvement_areas', [])
    
    def _calculate_engagement_level(self, analytics_data: dict) -> int:
        """Calculate overall engagement level from various metrics"""
        engagement_factors = [
            analytics_data.get('questions_asked', 0) * 10,  # Questions show engagement
            analytics_data.get('complex_responses', 0) * 15,  # Complex responses show effort
            min(100, analytics_data.get('total_words_spoken', 0) / 5),  # Speaking volume
            analytics_data.get('conversation_flow_score', 0) * 0.5  # Flow indicates engagement
        ]
        return min(100, int(sum(engagement_factors)))
    
    def add_conversation_turn(self, user_message: str, ai_response: str, analytics: dict = None):
        """Add a conversation turn to the transcript"""
        if not self.conversation_transcript:
            self.conversation_transcript = []
        
        turn_data = {
            'turn_number': len(self.conversation_transcript) + 1,
            'timestamp': datetime.utcnow().isoformat(),
            'user_message': user_message,
            'ai_response': ai_response,
            'user_word_count': len(user_message.split()),
            'ai_word_count': len(ai_response.split())
        }
        
        if analytics:
            turn_data['analytics'] = analytics
        
        self.conversation_transcript.append(turn_data)
        
        # Update counters
        self.total_turns += 1
        self.student_words_count += len(user_message.split())
        self.avatar_words_count += len(ai_response.split())
    
    def get_conversation_summary(self) -> dict:
        """Get a summary of the conversation"""
        if not self.conversation_transcript:
            return {}
        
        return {
            'total_turns': self.total_turns,
            'student_words': self.student_words_count,
            'avatar_words': self.avatar_words_count,
            'avg_words_per_turn': round(self.student_words_count / max(self.total_turns, 1), 1),
            'duration_minutes': round(self.duration_seconds / 60, 1) if self.duration_seconds else 0,
            'topic': self.conversation_topic,
            'engagement_level': self.engagement_level
        }
    
    def to_dict(self, include_transcript: bool = False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'session_id': self.session_id,
            'student_id': self.student_id,
            'conversation_topic': self.conversation_topic,
            'platform': self.platform,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'is_active': self.is_active,
            'total_turns': self.total_turns,
            'student_words_count': self.student_words_count,
            'avatar_words_count': self.avatar_words_count,
            'fluency_score': self.fluency_score,
            'pronunciation_score': self.pronunciation_score,
            'logical_flow_score': self.logical_flow_score,
            'vocabulary_complexity': self.vocabulary_complexity,
            'engagement_level': self.engagement_level,
            'response_appropriateness': self.response_appropriateness,
            'grammar_accuracy': self.grammar_accuracy,
            'questions_asked': self.questions_asked,
            'complex_responses': self.complex_responses,
            'topic_adherence': self.topic_adherence,
            'achievements': self.achievements,
            'improvement_areas': self.improvement_areas,
            'future_recommendations': self.future_recommendations
        }
        
        if include_transcript:
            data['conversation_transcript'] = self.conversation_transcript
        
        return data

class ConversationTurn(db.Model):
    """Model for individual conversation turns (optional detailed storage)"""
    __tablename__ = 'conversation_turn'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_session_id = db.Column(db.Integer, db.ForeignKey('conversation_session.id'), nullable=False)
    turn_number = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Turn content
    user_message = db.Column(db.Text)
    ai_response = db.Column(db.Text)
    user_word_count = db.Column(db.Integer)
    ai_word_count = db.Column(db.Integer)
    
    # Turn-specific analytics
    pronunciation_score = db.Column(db.Float)  # For this specific turn
    response_time_seconds = db.Column(db.Float)  # Time to respond
    complexity_score = db.Column(db.Integer)  # Message complexity
    sentiment_score = db.Column(db.Float)  # Emotional tone
    
    # Audio data (if available)
    audio_file_path = db.Column(db.String(255))  # Path to stored audio
    audio_duration_seconds = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_session_id': self.conversation_session_id,
            'turn_number': self.turn_number,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'user_word_count': self.user_word_count,
            'ai_word_count': self.ai_word_count,
            'pronunciation_score': self.pronunciation_score,
            'response_time_seconds': self.response_time_seconds,
            'complexity_score': self.complexity_score,
            'sentiment_score': self.sentiment_score,
            'audio_duration_seconds': self.audio_duration_seconds
        }