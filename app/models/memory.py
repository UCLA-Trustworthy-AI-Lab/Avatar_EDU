from datetime import datetime
from app import db

class StudentMemoryBoard(db.Model):
    """
    Compressed memory board that stores student learning patterns across all modules.
    Acts like a teacher's mental model - remembering mistakes, patterns, and progress.
    """
    __tablename__ = 'student_memory_board'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, unique=True)

    # Compressed module-specific memory (JSON format)
    reading_memory = db.Column(db.JSON, default=dict)
    listening_memory = db.Column(db.JSON, default=dict)
    speaking_memory = db.Column(db.JSON, default=dict)
    writing_memory = db.Column(db.JSON, default=dict)
    conversation_memory = db.Column(db.JSON, default=dict)

    # Cross-module insights
    overall_patterns = db.Column(db.JSON, default=dict)  # Common issues across modules

    # Compression tracking
    reading_last_compressed_at = db.Column(db.DateTime)
    listening_last_compressed_at = db.Column(db.DateTime)
    speaking_last_compressed_at = db.Column(db.DateTime)
    writing_last_compressed_at = db.Column(db.DateTime)
    conversation_last_compressed_at = db.Column(db.DateTime)

    # Session counters (trigger compression after N sessions)
    reading_sessions_since_compression = db.Column(db.Integer, default=0)
    listening_sessions_since_compression = db.Column(db.Integer, default=0)
    speaking_sessions_since_compression = db.Column(db.Integer, default=0)
    writing_sessions_since_compression = db.Column(db.Integer, default=0)
    conversation_sessions_since_compression = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReadingMemoryInsight(db.Model):
    """
    Raw, uncompressed insights from individual reading sessions.
    These get aggregated and compressed into StudentMemoryBoard periodically.
    """
    __tablename__ = 'reading_memory_insight'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    reading_session_id = db.Column(db.Integer, db.ForeignKey('reading_session.id'), nullable=False)

    # Vocabulary mistakes and patterns
    vocabulary_mistakes = db.Column(db.JSON, default=list)  # Words looked up multiple times
    difficult_words = db.Column(db.JSON, default=list)  # Words marked as difficult
    repeated_lookups = db.Column(db.JSON, default=list)  # Words looked up in previous sessions too

    # Comprehension issues
    incorrect_questions = db.Column(db.JSON, default=list)  # Questions answered incorrectly
    question_types_struggled = db.Column(db.JSON, default=list)  # Types: inference, main_idea, detail, etc.
    correct_questions = db.Column(db.JSON, default=list)  # Questions answered correctly

    # Chatbot interaction patterns (NEW - shows what confuses students)
    chatbot_questions_asked = db.Column(db.JSON, default=list)  # What they asked the AI
    chatbot_topics_confused = db.Column(db.JSON, default=list)  # Topics they needed help with
    chatbot_repeated_topics = db.Column(db.JSON, default=list)  # Topics asked about multiple times

    # Reading patterns
    reading_speed_issue = db.Column(db.Boolean, default=False)  # Too slow/fast
    completion_rate = db.Column(db.Float)  # Did they finish the text?
    engagement_level = db.Column(db.String(20))  # High/medium/low based on interactions

    # Text characteristics (to identify topic/difficulty patterns)
    text_category = db.Column(db.String(50))
    text_difficulty = db.Column(db.String(20))
    text_topic = db.Column(db.String(100))

    # GPT-extracted summary (generated at session end)
    ai_summary = db.Column(db.Text)  # "Student struggled with inference questions and abstract vocabulary"
    key_issues = db.Column(db.JSON, default=list)  # ["inference_questions", "abstract_vocabulary", "passive_voice"]

    # Compression status
    is_compressed = db.Column(db.Boolean, default=False)  # Has this been merged into memory board?
    compressed_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ListeningMemoryInsight(db.Model):
    """
    Raw insights from individual listening sessions.
    Tracks audio comprehension patterns, accent difficulties, speed issues.
    """
    __tablename__ = 'listening_memory_insight'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('learning_sessions.id'), nullable=True)

    # Question performance
    incorrect_questions = db.Column(db.JSON, default=list)
    question_types_struggled = db.Column(db.JSON, default=list)
    correct_questions = db.Column(db.JSON, default=list)

    # Listening challenges
    audio_category = db.Column(db.String(50))  # conversation, lecture, news
    audio_difficulty = db.Column(db.String(20))
    audio_speed_issue = db.Column(db.Boolean, default=False)

    # AI-extracted summary
    ai_summary = db.Column(db.Text)
    key_issues = db.Column(db.JSON, default=list)

    # Compression status
    is_compressed = db.Column(db.Boolean, default=False)
    compressed_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SpeakingMemoryInsight(db.Model):
    """
    Raw insights from individual speaking sessions.
    Tracks pronunciation errors, fluency issues, specific phoneme problems.
    """
    __tablename__ = 'speaking_memory_insight'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    speaking_session_id = db.Column(db.Integer, db.ForeignKey('speaking_sessions.id'), nullable=True)

    # Pronunciation patterns
    mispronounced_words = db.Column(db.JSON, default=list)  # Words consistently mispronounced
    phoneme_errors = db.Column(db.JSON, default=list)  # Specific sounds (th, r, l, etc.)
    accuracy_scores = db.Column(db.JSON, default=dict)  # Historical scores

    # Fluency issues
    fluency_problems = db.Column(db.JSON, default=list)  # Pausing, hesitation, speed

    # Practice level
    practice_level = db.Column(db.String(20))  # word/sentence/paragraph/ielts

    # AI-extracted summary
    ai_summary = db.Column(db.Text)
    key_issues = db.Column(db.JSON, default=list)

    # Compression status
    is_compressed = db.Column(db.Boolean, default=False)
    compressed_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class WritingMemoryInsight(db.Model):
    """
    Raw insights from individual writing sessions.
    Tracks grammar errors, style issues, vocabulary problems.
    """
    __tablename__ = 'writing_memory_insight'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    learning_session_id = db.Column(db.Integer, db.ForeignKey('learning_sessions.id'), nullable=True)

    # Writing characteristics
    writing_type = db.Column(db.String(50))  # academic, creative, business, etc.
    topic = db.Column(db.String(200))  # Writing topic/prompt

    # Grammar and style issues
    grammar_errors = db.Column(db.JSON, default=list)  # Repeated grammar mistakes
    style_issues = db.Column(db.JSON, default=list)  # Wordiness, passive voice, etc.
    vocabulary_issues = db.Column(db.JSON, default=list)  # Repetitive words, wrong word choice
    sentence_issues = db.Column(db.JSON, default=list)  # Sentence-level problems
    content_weaknesses = db.Column(db.JSON, default=list)  # Content-related issues

    # Scores
    overall_score = db.Column(db.Integer)  # Overall writing score
    on_topic = db.Column(db.Boolean, default=True)  # Whether writing was on topic

    # AI-extracted summary
    ai_summary = db.Column(db.Text)
    key_issues = db.Column(db.JSON, default=list)

    # Compression status
    is_compressed = db.Column(db.Boolean, default=False)
    compressed_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ConversationMemoryInsight(db.Model):
    """
    Raw insights from individual conversation sessions.
    Tracks communication patterns, topic struggles, engagement issues.
    """
    __tablename__ = 'conversation_memory_insight'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    conversation_session_id = db.Column(db.Integer, db.ForeignKey('conversation_session.id'), nullable=True)

    # Conversation patterns
    topic = db.Column(db.String(100))
    vocabulary_gaps = db.Column(db.JSON, default=list)  # Words student couldn't use
    grammar_errors = db.Column(db.JSON, default=list)
    fluency_issues = db.Column(db.JSON, default=list)

    # Pronunciation patterns (from audio conversations)
    mispronounced_words = db.Column(db.JSON, default=list)  # Words mispronounced
    phoneme_errors = db.Column(db.JSON, default=list)  # Specific sound errors
    pronunciation_scores = db.Column(db.JSON, default=dict)  # Pronunciation metrics

    # Topic struggles
    topic_struggles = db.Column(db.JSON, default=list)  # Topics they had difficulty with

    # Engagement
    engagement_level = db.Column(db.String(20))
    response_appropriateness = db.Column(db.Integer)  # Score

    # Session metrics
    total_messages = db.Column(db.Integer, default=0)
    total_words = db.Column(db.Integer, default=0)
    avg_words_per_message = db.Column(db.Float, default=0.0)

    # AI-extracted summary
    ai_summary = db.Column(db.Text)
    key_issues = db.Column(db.JSON, default=list)

    # Compression status
    is_compressed = db.Column(db.Boolean, default=False)
    compressed_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
