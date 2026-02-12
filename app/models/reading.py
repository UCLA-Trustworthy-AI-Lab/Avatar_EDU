from datetime import datetime
from app import db

class ReadingSession(db.Model):
    """Model for individual reading sessions"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('learning_sessions.id'), nullable=True)
    text_title = db.Column(db.String(200), nullable=False)
    text_content = db.Column(db.Text)  # Full text content or reference ID
    text_difficulty_level = db.Column(db.String(20))  # beginner/intermediate/advanced/expert
    text_category = db.Column(db.String(50))  # academic paper, news, literature, TOEFL material
    words_per_minute = db.Column(db.Float)
    total_words_read = db.Column(db.Integer)
    time_spent_reading = db.Column(db.Integer)  # Total reading time in seconds
    comprehension_score = db.Column(db.Integer)  # Understanding score (0-100)
    vocabulary_clicks = db.Column(db.Integer, default=0)  # Number of words clicked for definitions
    new_words_learned = db.Column(db.Integer, default=0)  # Count of new academic vocabulary encountered
    chinese_translations_used = db.Column(db.Integer, default=0)  # Count of times Chinese translation was accessed
    questions_answered = db.Column(db.Integer, default=0)  # Number of comprehension questions completed
    questions_correct = db.Column(db.Integer, default=0)  # Number of correct answers
    reading_completion_percentage = db.Column(db.Float, default=0.0)  # How much of text was read (0-100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class VocabularyInteraction(db.Model):
    """Model for tracking word clicks and vocabulary learning"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    reading_session_id = db.Column(db.Integer, db.ForeignKey('reading_session.id'), nullable=False)
    word = db.Column(db.String(100), nullable=False)  # The word that was clicked
    word_definition = db.Column(db.Text)  # Definition shown to student
    pronunciation = db.Column(db.String(200))  # IPA pronunciation guide
    examples = db.Column(db.JSON)  # JSON array of usage examples
    synonyms = db.Column(db.JSON)  # JSON array of related words
    chinese_translation = db.Column(db.String(200))  # Chinese translation if requested
    difficulty_level = db.Column(db.Integer)  # Word complexity (1-10)
    frequency_rank = db.Column(db.Integer)  # How common the word is (1-10000)
    interaction_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    looked_up_count = db.Column(db.Integer, default=1)  # How many times student looked up this word
    is_mastered = db.Column(db.Boolean, default=False)  # Whether student has learned this word
    
    # Composite unique constraint to prevent duplicate word lookups in same session
    __table_args__ = (db.UniqueConstraint('student_id', 'reading_session_id', 'word'),)

class ReadingProgress(db.Model):
    """Model for tracking long-term reading progress and vocabulary growth"""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, unique=True)
    total_words_read = db.Column(db.Integer, default=0)  # Cumulative word count
    average_reading_speed = db.Column(db.Float, default=0.0)  # Current WPM average
    vocabulary_size = db.Column(db.Integer, default=0)  # Estimated known vocabulary count
    difficult_words = db.Column(db.JSON)  # JSON array of challenging words
    mastered_words = db.Column(db.JSON)  # JSON array of learned vocabulary
    reading_level = db.Column(db.String(20))  # Current assessed reading level
    favorite_topics = db.Column(db.JSON)  # JSON array of preferred reading subjects
    comprehension_trend = db.Column(db.String(20))  # Recent performance trend (improving/stable/declining)
    last_reading_session = db.Column(db.DateTime)  # Timestamp of most recent reading
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ReadingMaterial(db.Model):
    """Model for storing reading materials and texts"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    difficulty_level = db.Column(db.String(20))  # beginner/intermediate/advanced/expert
    category = db.Column(db.String(50))  # academic, news, literature, TOEFL, etc.
    source = db.Column(db.String(200))  # Source URL or reference
    word_count = db.Column(db.Integer)
    estimated_reading_time = db.Column(db.Integer)  # in minutes
    tags = db.Column(db.JSON)  # JSON array of tags for searching/filtering
    target_exams = db.Column(db.JSON)  # JSON array of relevant exams (TOEFL, IELTS, etc.)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)  # Optional teacher who added it
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ComprehensionQuestion(db.Model):
    """Model for storing comprehension questions for reading materials"""
    id = db.Column(db.Integer, primary_key=True)
    reading_material_id = db.Column(db.Integer, db.ForeignKey('reading_material.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20))  # multiple_choice, short_answer, essay
    options = db.Column(db.JSON)  # JSON array for multiple choice options
    correct_answer = db.Column(db.Text)
    explanation = db.Column(db.Text)  # Explanation of the correct answer
    difficulty_level = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ReadingResponse(db.Model):
    """Model for storing student responses to comprehension questions"""
    id = db.Column(db.Integer, primary_key=True)
    reading_session_id = db.Column(db.Integer, db.ForeignKey('reading_session.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('comprehension_question.id'), nullable=False)
    student_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    score = db.Column(db.Integer)  # For partial credit answers
    time_spent = db.Column(db.Integer)  # Time spent on this question in seconds
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatbotInteraction(db.Model):
    """Model for tracking AI chatbot interactions during reading sessions"""
    __tablename__ = 'chatbot_interaction'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    reading_session_id = db.Column(db.Integer, db.ForeignKey('reading_session.id'), nullable=False)

    # Interaction details
    user_message = db.Column(db.Text, nullable=False)  # What the student asked
    chatbot_response = db.Column(db.Text, nullable=False)  # What the AI responded
    message_type = db.Column(db.String(50))  # general, word_explanation, comprehension, reading_help

    # Context analysis
    topic_category = db.Column(db.String(100))  # Extracted topic (grammar, vocabulary, comprehension, etc.)
    confusion_level = db.Column(db.String(20))  # low, medium, high (based on question phrasing)
    is_repeated_topic = db.Column(db.Boolean, default=False)  # Did they ask about this topic before?

    # Memory awareness
    memory_context_used = db.Column(db.Boolean, default=False)  # Did chatbot use memory board?

    created_at = db.Column(db.DateTime, default=datetime.utcnow)