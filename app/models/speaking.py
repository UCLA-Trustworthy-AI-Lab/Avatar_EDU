from datetime import datetime
from app import db
from typing import Dict, List, Optional
import json

class SpeakingSession(db.Model):
    __tablename__ = 'speaking_sessions'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('learning_sessions.id'), nullable=False)

    # Three sub-sections
    practice_type = db.Column(db.String(50), nullable=False)  # 'word', 'sentence', 'paragraph'
    difficulty_level = db.Column(db.String(20), default='intermediate')  # beginner, intermediate, advanced, expert

    # Content being practiced
    practice_content = db.Column(db.Text, nullable=False)  # The text to be spoken
    content_category = db.Column(db.String(100))  # vocabulary, daily_conversation, academic, business, etc.

    # Recording details
    audio_file_path = db.Column(db.String(500))
    recording_duration = db.Column(db.Float)  # in seconds

    # Azure Speech Assessment Scores
    pronunciation_score = db.Column(db.Float, default=0)  # 0-100
    accuracy_score = db.Column(db.Float, default=0)  # 0-100
    fluency_score = db.Column(db.Float, default=0)  # 0-100
    completeness_score = db.Column(db.Float, default=0)  # 0-100
    prosody_score = db.Column(db.Float, default=0)  # 0-100 (for sentences and paragraphs)

    # Detailed Analysis
    word_level_analysis = db.Column(db.JSON)  # Detailed word-by-word breakdown
    phoneme_analysis = db.Column(db.JSON)  # Phoneme-level pronunciation details
    problem_words = db.Column(db.JSON)  # List of words with pronunciation issues

    # Speech Features
    words_per_minute = db.Column(db.Float)
    pause_count = db.Column(db.Integer, default=0)
    filler_word_count = db.Column(db.Integer, default=0)  # um, uh, etc.

    # Feedback and Recommendations
    ai_feedback = db.Column(db.Text)
    improvement_suggestions = db.Column(db.JSON)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # Relationships
    student = db.relationship('Student', backref='speaking_sessions')
    session = db.relationship('LearningSession', backref='speaking_session_data')

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'student_id': self.student_id,
            'practice_type': self.practice_type,
            'difficulty_level': self.difficulty_level,
            'practice_content': self.practice_content,
            'content_category': self.content_category,
            'pronunciation_score': self.pronunciation_score,
            'accuracy_score': self.accuracy_score,
            'fluency_score': self.fluency_score,
            'completeness_score': self.completeness_score,
            'prosody_score': self.prosody_score,
            'words_per_minute': self.words_per_minute,
            'problem_words': self.problem_words,
            'ai_feedback': self.ai_feedback,
            'improvement_suggestions': self.improvement_suggestions,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def calculate_overall_score(self) -> float:
        """Calculate overall speaking performance score"""
        scores = [self.pronunciation_score, self.accuracy_score, self.fluency_score, self.completeness_score]
        if self.prosody_score > 0:  # Include prosody for sentences and paragraphs
            scores.append(self.prosody_score)
        return sum(scores) / len(scores) if scores else 0


class SpeakingPracticeContent(db.Model):
    """Pre-defined content for speaking practice"""
    __tablename__ = 'speaking_practice_content'

    id = db.Column(db.Integer, primary_key=True)
    practice_type = db.Column(db.String(50), nullable=False)  # 'word', 'sentence', 'paragraph'
    content_text = db.Column(db.Text, nullable=False)
    phonetic_transcription = db.Column(db.String(500))  # IPA transcription for words

    # Categorization
    difficulty_level = db.Column(db.String(20), default='intermediate')
    category = db.Column(db.String(100))  # vocabulary type, topic, etc.
    academic_level = db.Column(db.String(50))  # high_school, undergraduate, graduate

    # For exam preparation
    exam_type = db.Column(db.String(50))  # TOEFL, IELTS, GRE, etc.

    # Additional context
    context_hint = db.Column(db.Text)  # Usage context or meaning
    chinese_translation = db.Column(db.Text)  # For Chinese students

    # Audio reference (native speaker recording)
    reference_audio_url = db.Column(db.String(500))

    # Practice metadata
    usage_count = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'practice_type': self.practice_type,
            'content_text': self.content_text,
            'phonetic_transcription': self.phonetic_transcription,
            'difficulty_level': self.difficulty_level,
            'category': self.category,
            'context_hint': self.context_hint,
            'chinese_translation': self.chinese_translation,
            'reference_audio_url': self.reference_audio_url,
            'exam_type': self.exam_type
        }


class WordPronunciationHistory(db.Model):
    """Track student's pronunciation history for individual words"""
    __tablename__ = 'word_pronunciation_history'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    word = db.Column(db.String(100), nullable=False)

    # Tracking scores over time
    attempts = db.Column(db.Integer, default=1)
    best_score = db.Column(db.Float, default=0)
    latest_score = db.Column(db.Float, default=0)
    average_score = db.Column(db.Float, default=0)

    # Phoneme-level tracking
    problem_phonemes = db.Column(db.JSON)  # List of consistently problematic phonemes

    # Progress tracking
    is_mastered = db.Column(db.Boolean, default=False)  # Score consistently > 85
    first_attempt_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_practice_date = db.Column(db.DateTime, default=datetime.utcnow)
    mastery_date = db.Column(db.DateTime)

    # Relationship
    student = db.relationship('Student', backref='word_pronunciation_history')

    def update_with_new_attempt(self, new_score: float, phoneme_issues: List = None):
        """Update history with new pronunciation attempt"""
        self.attempts += 1
        self.latest_score = new_score
        self.best_score = max(self.best_score, new_score)
        self.average_score = ((self.average_score * (self.attempts - 1)) + new_score) / self.attempts
        self.last_practice_date = datetime.utcnow()

        # Check mastery (3 consecutive attempts > 85)
        if new_score >= 85:
            if self.attempts >= 3 and self.average_score >= 85:
                self.is_mastered = True
                self.mastery_date = datetime.utcnow()

        # Update problem phonemes
        if phoneme_issues:
            current_issues = self.problem_phonemes or []
            self.problem_phonemes = list(set(current_issues + phoneme_issues))

    def to_dict(self) -> Dict:
        return {
            'word': self.word,
            'attempts': self.attempts,
            'best_score': self.best_score,
            'latest_score': self.latest_score,
            'average_score': self.average_score,
            'is_mastered': self.is_mastered,
            'problem_phonemes': self.problem_phonemes,
            'last_practice_date': self.last_practice_date.isoformat() if self.last_practice_date else None
        }


class SpeakingChallenge(db.Model):
    """Daily or weekly speaking challenges for students"""
    __tablename__ = 'speaking_challenges'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    # Challenge type and content
    challenge_type = db.Column(db.String(50))  # daily, weekly, exam_prep
    practice_types = db.Column(db.JSON)  # ['word', 'sentence', 'paragraph']
    content_ids = db.Column(db.JSON)  # List of SpeakingPracticeContent IDs

    # Requirements
    minimum_score = db.Column(db.Float, default=75)
    required_attempts = db.Column(db.Integer, default=1)
    time_limit_minutes = db.Column(db.Integer)

    # Rewards
    points_reward = db.Column(db.Integer, default=10)
    badge_name = db.Column(db.String(100))

    # Scheduling
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'challenge_type': self.challenge_type,
            'practice_types': self.practice_types,
            'minimum_score': self.minimum_score,
            'points_reward': self.points_reward,
            'badge_name': self.badge_name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None
        }


class StudentSpeakingChallenge(db.Model):
    """Track student progress in speaking challenges"""
    __tablename__ = 'student_speaking_challenges'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('speaking_challenges.id'), nullable=False)

    # Progress tracking
    status = db.Column(db.String(50), default='not_started')  # not_started, in_progress, completed
    attempts_made = db.Column(db.Integer, default=0)
    best_score = db.Column(db.Float, default=0)

    # Completion details
    completed_at = db.Column(db.DateTime)
    points_earned = db.Column(db.Integer, default=0)
    badge_earned = db.Column(db.Boolean, default=False)

    # Relationships
    student = db.relationship('Student', backref='speaking_challenges')
    challenge = db.relationship('SpeakingChallenge', backref='student_attempts')

    def to_dict(self) -> Dict:
        return {
            'challenge_id': self.challenge_id,
            'status': self.status,
            'attempts_made': self.attempts_made,
            'best_score': self.best_score,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'points_earned': self.points_earned,
            'badge_earned': self.badge_earned
        }