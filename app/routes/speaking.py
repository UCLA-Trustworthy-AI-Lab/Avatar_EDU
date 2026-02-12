from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import tempfile
from app.services.enhanced_speaking_service import EnhancedSpeakingService
from app.models.user import Student
from app.models.session import LearningSession
from app.api.azure_speech_client import AzureSpeechClient
from app import db
import logging

logger = logging.getLogger(__name__)

# Create Blueprint
speaking_bp = Blueprint('speaking', __name__, url_prefix='/api/speaking')

def get_speaking_service():
    """Get speaking service instance within application context"""
    from app.services.enhanced_speaking_service import EnhancedSpeakingService
    return EnhancedSpeakingService()

# Allowed audio file extensions
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'webm', 'ogg', 'm4a'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============ GENERAL ENDPOINTS ============

@speaking_bp.route('/start-session', methods=['POST'])
@jwt_required()
def start_speaking_session():
    """Start a new speaking practice session"""
    user_id = get_jwt_identity()
    data = request.get_json()

    practice_type = data.get('practice_type', 'word')  # word, sentence, or paragraph
    activity_type = data.get('activity_type', 'pronunciation')

    # Create learning session
    session = LearningSession(
        student_id=user_id,
        module_type='speaking',
        activity_type=f"{practice_type}_{activity_type}"
    )
    db.session.add(session)
    db.session.commit()

    return jsonify({
        'session_id': session.id,
        'practice_type': practice_type,
        'message': 'Speaking session started successfully'
    }), 201

@speaking_bp.route('/end-session/<int:session_id>', methods=['POST'])
@jwt_required()
def end_speaking_session(session_id):
    """End a speaking practice session"""
    user_id = get_jwt_identity()
    data = request.get_json()

    session = LearningSession.query.filter_by(
        id=session_id,
        student_id=user_id
    ).first()

    if not session:
        return jsonify({'error': 'Session not found'}), 404

    # Complete the session
    session.complete_session(
        score=data.get('overall_score', 0),
        data=data
    )
    db.session.commit()

    return jsonify({
        'message': 'Session completed successfully',
        'session_id': session_id,
        'score': session.performance_score
    }), 200

# ============ WORD PRACTICE ENDPOINTS ============

@speaking_bp.route('/words/practice-content', methods=['GET'])
@jwt_required()
def get_word_practice_content():
    """Get words for pronunciation practice"""
    difficulty = request.args.get('difficulty', 'intermediate')
    category = request.args.get('category', 'academic_vocabulary')
    count = request.args.get('count', 10, type=int)
    content_source = request.args.get('source', 'database')  # 'database' or 'ai'

    speaking_service = get_speaking_service()

    if content_source == 'database':
        # Get existing content from database first
        words = speaking_service.get_database_word_content(
            difficulty_level=difficulty,
            category=category,
            count=count
        )
    else:
        # Generate new content with AI
        words = speaking_service.get_word_practice_content(
            difficulty_level=difficulty,
            category=category,
            count=count
        )

    # Convert to dictionaries for JSON serialization
    words_data = [word.to_dict() if hasattr(word, 'to_dict') else word for word in words]

    return jsonify({
        'practice_type': 'word',
        'content': words_data,
        'count': len(words_data),
        'source': content_source
    }), 200

@speaking_bp.route('/words/assess', methods=['POST'])
@jwt_required()
def assess_word_pronunciation():
    """Assess pronunciation of a single word"""
    user_id = get_jwt_identity()

    # Check if audio file is present
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    if not allowed_file(audio_file.filename):
        return jsonify({'error': 'Invalid audio file format'}), 400

    # Get other form data
    target_word = request.form.get('target_word')
    session_id = request.form.get('session_id', type=int)

    if not target_word or not session_id:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Save audio file temporarily
    temp_dir = tempfile.mkdtemp()
    filename = secure_filename(audio_file.filename)
    audio_path = os.path.join(temp_dir, filename)
    audio_file.save(audio_path)

    try:
        # Assess pronunciation
        speaking_service = get_speaking_service()
        result = speaking_service.assess_word_pronunciation(
            student_id=user_id,
            audio_file_path=audio_path,
            target_word=target_word,
            session_id=session_id
        )

        return jsonify(result), 200

    finally:
        # Clean up temp file
        if os.path.exists(audio_path):
            os.remove(audio_path)
        os.rmdir(temp_dir)

@speaking_bp.route('/words/history', methods=['GET'])
@jwt_required()
def get_word_pronunciation_history():
    """Get student's word pronunciation history"""
    user_id = get_jwt_identity()

    from app.models.speaking import WordPronunciationHistory

    history = WordPronunciationHistory.query.filter_by(
        student_id=user_id
    ).order_by(WordPronunciationHistory.last_practice_date.desc()).limit(50).all()

    return jsonify({
        'history': [h.to_dict() for h in history],
        'total_words_practiced': len(history)
    }), 200

@speaking_bp.route('/words/problem-areas', methods=['GET'])
@jwt_required()
def get_problem_words():
    """Get words that need more practice"""
    user_id = get_jwt_identity()

    from app.models.speaking import WordPronunciationHistory

    problem_words = WordPronunciationHistory.query.filter_by(
        student_id=user_id,
        is_mastered=False
    ).order_by(WordPronunciationHistory.average_score).limit(20).all()

    return jsonify({
        'problem_words': [w.to_dict() for w in problem_words],
        'count': len(problem_words)
    }), 200

# ============ SENTENCE PRACTICE ENDPOINTS ============

@speaking_bp.route('/sentences/practice-content', methods=['GET'])
@jwt_required()
def get_sentence_practice_content():
    """Get sentences for pronunciation and intonation practice"""
    difficulty = request.args.get('difficulty', 'intermediate')
    category = request.args.get('category', 'daily_conversation')
    count = request.args.get('count', 5, type=int)

    speaking_service = get_speaking_service()
    sentences = speaking_service.get_sentence_practice_content(
        difficulty_level=difficulty,
        category=category,
        count=count
    )

    return jsonify({
        'practice_type': 'sentence',
        'content': sentences,
        'count': len(sentences)
    }), 200

@speaking_bp.route('/sentences/assess', methods=['POST'])
@jwt_required()
def assess_sentence_pronunciation():
    """Assess pronunciation of a sentence"""
    user_id = get_jwt_identity()

    # Check if audio file is present
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    if not allowed_file(audio_file.filename):
        return jsonify({'error': 'Invalid audio file format'}), 400

    # Get other form data
    target_sentence = request.form.get('target_sentence')
    session_id = request.form.get('session_id', type=int)

    if not target_sentence or not session_id:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Save audio file temporarily
    temp_dir = tempfile.mkdtemp()
    filename = secure_filename(audio_file.filename)
    audio_path = os.path.join(temp_dir, filename)
    audio_file.save(audio_path)

    try:
        # Assess pronunciation
        speaking_service = get_speaking_service()
        result = speaking_service.assess_sentence_pronunciation(
            student_id=user_id,
            audio_file_path=audio_path,
            target_sentence=target_sentence,
            session_id=session_id
        )

        return jsonify(result), 200

    finally:
        # Clean up temp file
        if os.path.exists(audio_path):
            os.remove(audio_path)
        os.rmdir(temp_dir)

# ============ PARAGRAPH PRACTICE ENDPOINTS ============

@speaking_bp.route('/paragraphs/practice-content', methods=['GET'])
@jwt_required()
def get_paragraph_practice_content():
    """Get paragraph for extended speaking practice"""
    difficulty = request.args.get('difficulty', 'intermediate')
    category = request.args.get('category', 'self_introduction')
    exam_type = request.args.get('exam_type')  # Optional: TOEFL, IELTS, etc.

    speaking_service = get_speaking_service()
    paragraph = speaking_service.get_paragraph_practice_content(
        difficulty_level=difficulty,
        category=category,
        exam_type=exam_type
    )

    return jsonify({
        'practice_type': 'paragraph',
        'content': paragraph
    }), 200

@speaking_bp.route('/paragraphs/assess', methods=['POST'])
@jwt_required()
def assess_paragraph_pronunciation():
    """Assess extended speech (paragraph)"""
    user_id = get_jwt_identity()

    # Check if audio file is present
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    if not allowed_file(audio_file.filename):
        return jsonify({'error': 'Invalid audio file format'}), 400

    # Get other form data
    target_paragraph = request.form.get('target_paragraph')
    session_id = request.form.get('session_id', type=int)

    if not target_paragraph or not session_id:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Save audio file temporarily
    temp_dir = tempfile.mkdtemp()
    filename = secure_filename(audio_file.filename)
    audio_path = os.path.join(temp_dir, filename)
    audio_file.save(audio_path)

    try:
        # Assess pronunciation
        speaking_service = get_speaking_service()
        result = speaking_service.assess_paragraph_pronunciation(
            student_id=user_id,
            audio_file_path=audio_path,
            target_paragraph=target_paragraph,
            session_id=session_id
        )

        return jsonify(result), 200

    finally:
        # Clean up temp file
        if os.path.exists(audio_path):
            os.remove(audio_path)
        os.rmdir(temp_dir)

# ============ PROGRESS & ANALYTICS ENDPOINTS ============

@speaking_bp.route('/progress/summary', methods=['GET'])
@jwt_required()
def get_speaking_progress():
    """Get comprehensive speaking progress summary"""
    user_id = get_jwt_identity()

    speaking_service = get_speaking_service()
    summary = speaking_service.get_student_progress_summary(user_id)

    return jsonify(summary), 200

# ============ UNIFIED ASSESSMENT ENDPOINT ============

@speaking_bp.route('/assess-pronunciation', methods=['POST'])
@jwt_required()
def assess_pronunciation():
    """Unified pronunciation assessment for all practice types"""
    user_id = get_jwt_identity()

    # Check if audio file is present
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    if not audio_file or audio_file.filename == '':
        return jsonify({'error': 'No audio file selected'}), 400

    # Get form data
    reference_text = request.form.get('reference_text', '')
    practice_type = request.form.get('practice_type', 'word')

    if not reference_text:
        return jsonify({'error': 'Reference text is required'}), 400

    # Save audio file temporarily
    temp_dir = tempfile.mkdtemp()
    try:
        # Determine file extension based on uploaded file type
        original_filename = audio_file.filename or ''
        if original_filename.endswith('.wav'):
            filename = secure_filename(f"{practice_type}_recording.wav")
        elif original_filename.endswith('.webm'):
            filename = secure_filename(f"{practice_type}_recording.webm")
        else:
            # Default to webm for backwards compatibility
            filename = secure_filename(f"{practice_type}_recording.webm")

        if not filename:
            filename = f"{practice_type}_recording.webm"

        audio_path = os.path.join(temp_dir, filename)
        audio_file.save(audio_path)

        logger.info(f"Saved audio file: {audio_path}, size: {os.path.getsize(audio_path)} bytes")

        # Convert audio to WAV format for Azure compatibility if needed
        if filename.endswith('.wav'):
            # Already in WAV format
            wav_path = audio_path
            logger.info(f"Audio already in WAV format: {wav_path}")
        else:
            # Need to convert from WebM to WAV
            try:
                from app.utils.audio_converter import ensure_wav_format
                wav_path = ensure_wav_format(audio_path)
                logger.info(f"Converted audio to WAV format: {wav_path}")
            except Exception as conversion_error:
                logger.error(f"Audio conversion failed: {conversion_error}")
                # Use original file and let Azure handle the error
                wav_path = audio_path

        # Initialize Azure Speech Client
        azure_client = AzureSpeechClient()

        # Assess pronunciation using WAV file
        result = azure_client.assess_pronunciation(
            audio_file_path=wav_path,
            reference_text=reference_text,
            enable_prosody=practice_type in ['sentence', 'paragraph', 'ielts'],
            enable_content=practice_type in ['paragraph', 'ielts']
        )

        logger.info(f"Azure assessment result: {result}")

        if 'error' in result:
            # Provide fallback mock results
            logger.warning(f"Azure assessment failed: {result['error']}")
            result = create_mock_assessment_result(reference_text, practice_type)
        else:
            # Format the Azure result for frontend (with student_id for memory-aware feedback)
            result = format_assessment_result(result, practice_type, student_id=user_id)

        # Save to database if we have a session
        try:
            # Create LearningSession first
            from app.models.session import LearningSession
            from app.models.speaking import SpeakingSession

            # Create a learning session for this practice
            learning_session = LearningSession(
                student_id=user_id,
                module_type='speaking',
                activity_type=practice_type,
                performance_score=result.get('pronunciation_score', 0),
                is_completed=True
            )
            db.session.add(learning_session)
            db.session.flush()  # Get the ID

            # Create speaking session record
            speaking_session = SpeakingSession(
                student_id=user_id,
                session_id=learning_session.id,
                practice_type=practice_type,
                practice_content=reference_text,
                pronunciation_score=result.get('pronunciation_score', 0),
                accuracy_score=result.get('accuracy_score', 0),
                fluency_score=result.get('fluency_score', 0),
                completeness_score=result.get('completeness_score', 0),
                ai_feedback=result.get('feedback', ''),
                word_level_analysis=result.get('word_analysis', {}),
                audio_file_path=wav_path  # Note: in production, save to persistent storage
            )

            db.session.add(speaking_session)
            db.session.commit()

            logger.info(f"Saved speaking session {speaking_session.id} with learning session {learning_session.id}")

            # === MEMORY BOARD INTEGRATION ===
            # Extract insights from this speaking session
            try:
                from app.services.memory_service import get_memory_service
                memory_service = get_memory_service()

                # Extract insights
                insight = memory_service.extract_speaking_session_insights(
                    student_id=user_id,
                    speaking_session_id=speaking_session.id
                )
                logger.info(f"Extracted speaking memory insights for session {speaking_session.id}")

                # Check if we should compress memory
                if memory_service.should_compress_speaking_memory(user_id):
                    logger.info(f"Compressing speaking memory for student {user_id}")
                    compressed = memory_service.compress_speaking_memory(
                        student_id=user_id,
                        use_ai=True
                    )
                    logger.info(f"Speaking memory compression complete. Summary: {compressed.get('summary', 'N/A')[:100]}")

            except Exception as mem_error:
                logger.error(f"Speaking memory tracking error (non-fatal): {mem_error}")
                # Don't fail the assessment if memory tracking fails

            # === END MEMORY BOARD INTEGRATION ===

        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
            db.session.rollback()
            # Continue even if DB save fails

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Assessment error: {str(e)}")
        # Return mock results on any error
        mock_result = create_mock_assessment_result(reference_text, practice_type)
        return jsonify(mock_result), 200

    finally:
        # Clean up temp files
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception as cleanup_error:
            logger.error(f"Cleanup error: {cleanup_error}")

def create_mock_assessment_result(reference_text, practice_type):
    """Create mock assessment results when Azure is not available"""
    import random

    # Generate realistic mock scores
    base_score = random.randint(75, 90)
    pronunciation_score = base_score + random.randint(-5, 5)
    accuracy_score = base_score + random.randint(-3, 7)
    fluency_score = base_score + random.randint(-8, 8)
    completeness_score = base_score + random.randint(-2, 10)

    # Ensure scores are within 0-100 range
    pronunciation_score = max(0, min(100, pronunciation_score))
    accuracy_score = max(0, min(100, accuracy_score))
    fluency_score = max(0, min(100, fluency_score))
    completeness_score = max(0, min(100, completeness_score))

    overall_score = (pronunciation_score + accuracy_score + fluency_score + completeness_score) / 4

    feedback_messages = {
        'word': [
            "Good pronunciation! Focus on clear articulation of each syllable.",
            "Well done! Try to emphasize the stressed syllables more clearly.",
            "Nice effort! Practice the consonant sounds for better clarity.",
            "Great job! Work on maintaining consistent volume throughout the word."
        ],
        'sentence': [
            "Good sentence flow! Work on natural intonation patterns.",
            "Well spoken! Try to pause appropriately between phrases.",
            "Nice rhythm! Focus on linking words smoothly together.",
            "Great expression! Practice varying your pitch for emphasis."
        ],
        'paragraph': [
            "Excellent fluency! Work on maintaining consistent pace throughout.",
            "Good coherence! Practice transitions between sentences.",
            "Well structured! Focus on emphasizing key points with intonation.",
            "Great delivery! Work on pausing for breath without breaking flow."
        ],
        'ielts': [
            "Strong response! Work on organizing ideas more clearly.",
            "Good content! Practice using more varied vocabulary.",
            "Well developed! Focus on providing specific examples.",
            "Great fluency! Work on pronunciation of complex words."
        ]
    }

    feedback = random.choice(feedback_messages.get(practice_type, feedback_messages['word']))

    return {
        'pronunciation_score': round(pronunciation_score, 1),
        'accuracy_score': round(accuracy_score, 1),
        'fluency_score': round(fluency_score, 1),
        'completeness_score': round(completeness_score, 1),
        'overall_score': round(overall_score, 1),
        'feedback': feedback,
        'recognized_text': reference_text[:50] + "..." if len(reference_text) > 50 else reference_text,
        'status': 'mock',
        'message': 'This is practice mode. For detailed AI assessment, please ensure Azure Speech Services are configured.'
    }

def format_assessment_result(azure_result, practice_type, student_id=None):
    """Format Azure assessment results with detailed educational insights"""

    # Extract scores from Azure result
    pronunciation_score = azure_result.get('PronScore', 0)
    accuracy_score = azure_result.get('AccuracyScore', 0)
    fluency_score = azure_result.get('FluencyScore', 0)
    completeness_score = azure_result.get('CompletenessScore', 0)

    overall_score = (pronunciation_score + accuracy_score + fluency_score + completeness_score) / 4

    # Analyze word-level details
    word_analysis = []
    problem_phonemes = []
    excellent_words = []

    if 'Words' in azure_result and azure_result['Words']:
        for word_data in azure_result['Words']:
            word = word_data.get('Word', '')
            word_accuracy = word_data.get('AccuracyScore', 0)
            # Handle None values from Azure (for omitted words)
            if word_accuracy is None:
                word_accuracy = 0
            error_type = word_data.get('ErrorType', 'None')

            word_info = {
                'word': word,
                'accuracy_score': word_accuracy,
                'error_type': error_type,
                'status': 'excellent' if word_accuracy >= 85 else 'needs_practice' if word_accuracy < 70 else 'good'
            }

            # Analyze phonemes if available
            if 'Phonemes' in word_data:
                phoneme_details = []
                for phoneme in word_data['Phonemes']:
                    phoneme_score = phoneme.get('AccuracyScore', 0)
                    # Handle None values for phoneme scores
                    if phoneme_score is None:
                        phoneme_score = 0
                    phoneme_sound = phoneme.get('Phoneme', '')

                    phoneme_details.append({
                        'phoneme': phoneme_sound,
                        'accuracy_score': phoneme_score
                    })

                    if phoneme_score < 70 and phoneme_sound:
                        problem_phonemes.append(phoneme_sound)

                word_info['phonemes'] = phoneme_details

            word_analysis.append(word_info)

            if word_accuracy >= 90:
                excellent_words.append(word)

    # === LOAD MEMORY FOR PERSONALIZED FEEDBACK ===
    speaking_memory = {}
    memory_aware = False
    if student_id:
        try:
            from app.services.memory_service import get_memory_service
            memory_service = get_memory_service()
            speaking_memory = memory_service.get_speaking_memory(student_id)
            memory_aware = bool(speaking_memory)
        except Exception as mem_error:
            logger.error(f"Error loading speaking memory: {mem_error}")
    # === END MEMORY LOAD ===

    # Generate comprehensive feedback
    feedback_parts = []
    performance_summary = []
    improvement_tips = []

    # Overall performance assessment
    if overall_score >= 90:
        performance_summary.append("🎉 Outstanding performance! Your pronunciation is exceptionally clear and natural.")
    elif overall_score >= 80:
        performance_summary.append("✅ Excellent pronunciation! Very fluent speech with accurate pronunciation.")
    elif overall_score >= 70:
        performance_summary.append("👍 Good pronunciation! You're speaking clearly and confidently.")
    elif overall_score >= 60:
        performance_summary.append("📈 Solid progress! Keep practicing to build more consistency.")
    else:
        performance_summary.append("🎯 Keep working at it! Focus on breaking down the sounds carefully.")

    # Detailed score analysis
    score_breakdown = []

    # Pronunciation analysis
    if pronunciation_score >= 85:
        score_breakdown.append(f"Pronunciation: Excellent ({pronunciation_score:.1f}/100) - Your articulation is very clear!")
    elif pronunciation_score >= 70:
        score_breakdown.append(f"Pronunciation: Good ({pronunciation_score:.1f}/100) - Some sounds could be clearer.")
    else:
        score_breakdown.append(f"Pronunciation: Needs improvement ({pronunciation_score:.1f}/100) - Focus on individual sound accuracy.")

    # Fluency analysis
    if fluency_score >= 85:
        score_breakdown.append(f"Fluency: Excellent ({fluency_score:.1f}/100) - Very natural rhythm and flow!")
    elif fluency_score >= 70:
        score_breakdown.append(f"Fluency: Good ({fluency_score:.1f}/100) - Practice maintaining consistent pace.")
    else:
        score_breakdown.append(f"Fluency: Developing ({fluency_score:.1f}/100) - Work on smoother speech patterns.")

    # Accuracy analysis
    if accuracy_score >= 85:
        score_breakdown.append(f"Accuracy: Excellent ({accuracy_score:.1f}/100) - Words are pronounced correctly!")
    elif accuracy_score >= 70:
        score_breakdown.append(f"Accuracy: Good ({accuracy_score:.1f}/100) - Minor pronunciation adjustments needed.")
    else:
        score_breakdown.append(f"Accuracy: Needs work ({accuracy_score:.1f}/100) - Focus on word-level pronunciation.")

    # Specific improvement recommendations
    if problem_phonemes:
        unique_phonemes = list(set(problem_phonemes[:3]))  # Top 3 unique problem sounds
        improvement_tips.append(f"🎯 Focus on these sounds: {', '.join(unique_phonemes)}")

        # Add specific phoneme tips
        phoneme_guidance = {
            'θ': "Practice 'th' by placing tongue between teeth (think, three)",
            'ð': "Practice voiced 'th' with tongue between teeth (this, that)",
            'r': "Curl tongue back slightly, don't touch roof of mouth",
            'l': "Touch tongue tip to ridge behind upper teeth",
            'v': "Upper teeth touch lower lip, vibrate vocal cords",
            'w': "Round lips first, then open while voicing",
            'ɪ': "Relaxed tongue position for short 'i' sound (sit, bit)",
            'iː': "Longer, tenser tongue position for long 'ee' sound (see, free)"
        }

        for phoneme in unique_phonemes:
            if phoneme in phoneme_guidance:
                improvement_tips.append(f"💡 {phoneme}: {phoneme_guidance[phoneme]}")

    # Positive reinforcement
    if excellent_words:
        performance_summary.append(f"🌟 Perfect pronunciation on: {', '.join(excellent_words[:3])}")

    # Practice recommendations based on practice type
    if practice_type == 'word':
        improvement_tips.append("🔄 Try practicing this word in different sentences")
        improvement_tips.append("🎵 Record yourself saying it slowly, then at normal speed")
    elif practice_type == 'sentence':
        improvement_tips.append("🔄 Practice reading similar sentences aloud daily")
        improvement_tips.append("🎵 Focus on linking words smoothly together")
    elif practice_type == 'paragraph' or practice_type == 'ielts':
        improvement_tips.append("🔄 Practice speaking on similar topics for 1-2 minutes")
        improvement_tips.append("🎵 Record yourself and listen for natural rhythm")

    # === MEMORY-AWARE PERSONALIZED TIPS ===
    if memory_aware and speaking_memory:
        chronic_words = speaking_memory.get('chronic_pronunciation_errors', [])
        problem_phonemes_memory = speaking_memory.get('problem_phonemes', [])
        memory_summary = speaking_memory.get('summary', '')

        if chronic_words:
            # Reference chronic pronunciation issues
            chronic_word_names = [w.get('word', '') for w in chronic_words[:2]]
            if chronic_word_names:
                improvement_tips.insert(0, f"🧠 I remember you're working on: {', '.join(chronic_word_names)}")

        if problem_phonemes_memory and not problem_phonemes:
            # If no issues today but history shows problems
            phoneme_names = [p.get('phoneme', '') for p in problem_phonemes_memory[:2]]
            if phoneme_names:
                performance_summary.append(f"✨ Great progress on {', '.join(phoneme_names)} sounds!")

        if memory_summary:
            # Add encouraging reference to their journey
            if overall_score >= 75:
                improvement_tips.append(f"📈 Your pronunciation is improving! Keep up the excellent work.")
    # === END MEMORY-AWARE TIPS ===

    # Combine all feedback
    feedback = " ".join(performance_summary + score_breakdown[:2])  # Main feedback

    return {
        'pronunciation_score': round(pronunciation_score, 1),
        'accuracy_score': round(accuracy_score, 1),
        'fluency_score': round(fluency_score, 1),
        'completeness_score': round(completeness_score, 1),
        'overall_score': round(overall_score, 1),
        'feedback': feedback,
        'memory_aware': memory_aware,  # NEW: Indicates if memory was used
        'detailed_feedback': {
            'performance_summary': performance_summary,
            'score_breakdown': score_breakdown,
            'improvement_tips': improvement_tips,
            'excellent_words': excellent_words,
            'problem_phonemes': list(set(problem_phonemes)) if problem_phonemes else []
        },
        'recognized_text': azure_result.get('RecognizedText', ''),
        'word_analysis': word_analysis,
        'status': 'azure',
        'message': 'Detailed assessment completed using Azure Speech Services with educational insights.'
    }

@speaking_bp.route('/progress/by-type', methods=['GET'])
@jwt_required()
def get_progress_by_practice_type():
    """Get progress breakdown by practice type"""
    user_id = get_jwt_identity()

    from app.models.speaking import SpeakingSession
    from sqlalchemy import func

    # Get stats for each practice type
    stats = db.session.query(
        SpeakingSession.practice_type,
        func.count(SpeakingSession.id).label('session_count'),
        func.avg(SpeakingSession.pronunciation_score).label('avg_pronunciation'),
        func.avg(SpeakingSession.fluency_score).label('avg_fluency'),
        func.avg(SpeakingSession.accuracy_score).label('avg_accuracy')
    ).filter_by(student_id=user_id).group_by(SpeakingSession.practice_type).all()

    progress_data = {}
    for stat in stats:
        progress_data[stat.practice_type] = {
            'sessions': stat.session_count,
            'avg_pronunciation': round(stat.avg_pronunciation or 0, 1),
            'avg_fluency': round(stat.avg_fluency or 0, 1),
            'avg_accuracy': round(stat.avg_accuracy or 0, 1)
        }

    return jsonify(progress_data), 200

@speaking_bp.route('/progress/recent-sessions', methods=['GET'])
@jwt_required()
def get_recent_speaking_sessions():
    """Get recent speaking practice sessions"""
    user_id = get_jwt_identity()
    limit = request.args.get('limit', 10, type=int)

    from app.models.speaking import SpeakingSession

    sessions = SpeakingSession.query.filter_by(
        student_id=user_id
    ).order_by(SpeakingSession.created_at.desc()).limit(limit).all()

    return jsonify({
        'sessions': [s.to_dict() for s in sessions],
        'count': len(sessions)
    }), 200

# ============ CHALLENGES ENDPOINTS ============

@speaking_bp.route('/challenges/daily', methods=['POST'])
@jwt_required()
def create_daily_challenge():
    """Create a personalized daily speaking challenge"""
    user_id = get_jwt_identity()

    speaking_service = get_speaking_service()
    challenge = speaking_service.create_daily_challenge(user_id)

    return jsonify(challenge), 201

@speaking_bp.route('/challenges/active', methods=['GET'])
@jwt_required()
def get_active_challenges():
    """Get active speaking challenges for the student"""
    user_id = get_jwt_identity()

    from app.models.speaking import StudentSpeakingChallenge
    from datetime import datetime

    active_challenges = StudentSpeakingChallenge.query.filter_by(
        student_id=user_id,
        status='in_progress'
    ).all()

    return jsonify({
        'challenges': [c.to_dict() for c in active_challenges],
        'count': len(active_challenges)
    }), 200

@speaking_bp.route('/challenges/<int:challenge_id>/complete', methods=['POST'])
@jwt_required()
def complete_challenge(challenge_id):
    """Mark a challenge as completed"""
    user_id = get_jwt_identity()
    data = request.get_json()

    from app.models.speaking import StudentSpeakingChallenge
    from datetime import datetime

    challenge = StudentSpeakingChallenge.query.filter_by(
        student_id=user_id,
        challenge_id=challenge_id
    ).first()

    if not challenge:
        return jsonify({'error': 'Challenge not found'}), 404

    # Update challenge status
    challenge.status = 'completed'
    challenge.completed_at = datetime.utcnow()
    challenge.best_score = data.get('score', 0)
    challenge.points_earned = challenge.challenge.points_reward

    db.session.commit()

    return jsonify({
        'message': 'Challenge completed successfully',
        'points_earned': challenge.points_earned
    }), 200

# ============ PHONEME TIPS ENDPOINT ============

@speaking_bp.route('/phonemes/tips', methods=['GET'])
def get_phoneme_tips():
    """Get pronunciation tips for common phonemes"""
    phoneme = request.args.get('phoneme')

    tips = {
        'θ': {
            'symbol': 'θ',
            'name': 'Voiceless th',
            'examples': ['think', 'three', 'math'],
            'tip': "Place your tongue between your teeth and blow air gently",
            'common_mistakes': "Often pronounced as 's' or 'f' by Chinese speakers"
        },
        'ð': {
            'symbol': 'ð',
            'name': 'Voiced th',
            'examples': ['this', 'that', 'mother'],
            'tip': "Similar to 'θ' but with voice vibration",
            'common_mistakes': "Often pronounced as 'd' or 'z' by Chinese speakers"
        },
        'r': {
            'symbol': 'r',
            'name': 'R sound',
            'examples': ['red', 'car', 'sorry'],
            'tip': "Curl your tongue back slightly, don't let it touch the roof of your mouth",
            'common_mistakes': "Often confused with 'l' sound by Chinese speakers"
        },
        'l': {
            'symbol': 'l',
            'name': 'L sound',
            'examples': ['like', 'ball', 'hello'],
            'tip': "Touch the tip of your tongue to the ridge behind your upper teeth",
            'common_mistakes': "Often confused with 'r' or 'n' sound"
        },
        'v': {
            'symbol': 'v',
            'name': 'V sound',
            'examples': ['very', 'have', 'love'],
            'tip': "Place your upper teeth on your lower lip and vibrate",
            'common_mistakes': "Often pronounced as 'w' by Chinese speakers"
        },
        'w': {
            'symbol': 'w',
            'name': 'W sound',
            'examples': ['we', 'water', 'away'],
            'tip': "Round your lips and then open them while voicing",
            'common_mistakes': "Often confused with 'v' sound"
        }
    }

    if phoneme and phoneme in tips:
        return jsonify(tips[phoneme]), 200

    return jsonify(tips), 200

# ============ TOPIC ANSWER PRACTICE ENDPOINTS ============

@speaking_bp.route('/topics/practice-content', methods=['GET'])
@jwt_required()
def get_topic_practice_content():
    """Get topics for IELTS-style speaking practice"""
    difficulty = request.args.get('difficulty', 'intermediate')
    category = request.args.get('category', 'general')
    content_source = request.args.get('source', 'database')  # 'database' or 'ai'

    speaking_service = get_speaking_service()

    if content_source == 'database':
        # Get existing topics from database
        topic = speaking_service.get_database_topic_content(
            difficulty_level=difficulty,
            category=category
        )
    else:
        # Generate new topic with AI
        topic = speaking_service.get_topic_practice_content(
            difficulty_level=difficulty,
            category=category
        )

    return jsonify({
        'practice_type': 'topic',
        'content': topic,
        'source': content_source
    }), 200

@speaking_bp.route('/topics/assess', methods=['POST'])
@jwt_required()
def assess_topic_answer():
    """Assess IELTS-style topic answer"""
    user_id = get_jwt_identity()

    # Check if audio file is present
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    if not allowed_file(audio_file.filename):
        return jsonify({'error': 'Invalid audio file format'}), 400

    # Get other form data
    topic_text = request.form.get('topic_text')
    session_id = request.form.get('session_id', type=int)
    preparation_time = request.form.get('preparation_time', 90, type=int)
    speaking_time = request.form.get('speaking_time', 60, type=int)

    if not topic_text or not session_id:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Save audio file temporarily
    temp_dir = tempfile.mkdtemp()
    filename = secure_filename(audio_file.filename)
    audio_path = os.path.join(temp_dir, filename)
    audio_file.save(audio_path)

    try:
        # Assess topic answer
        speaking_service = get_speaking_service()
        result = speaking_service.assess_topic_answer(
            student_id=user_id,
            audio_file_path=audio_path,
            topic_text=topic_text,
            session_id=session_id,
            preparation_time=preparation_time,
            speaking_time=speaking_time
        )

        return jsonify(result), 200

    finally:
        # Clean up temp file
        if os.path.exists(audio_path):
            os.remove(audio_path)
        os.rmdir(temp_dir)

# ============ PRACTICE CATEGORIES ENDPOINT ============

@speaking_bp.route('/categories', methods=['GET'])
def get_practice_categories():
    """Get available practice categories for each type"""
    return jsonify({
        'word': [
            {'id': 'academic_vocabulary', 'name': 'Academic Vocabulary', 'description': 'Common academic words'},
            {'id': 'toefl_words', 'name': 'TOEFL Vocabulary', 'description': 'Essential TOEFL words'},
            {'id': 'ielts_words', 'name': 'IELTS Vocabulary', 'description': 'Key IELTS vocabulary'},
            {'id': 'business_terms', 'name': 'Business Terms', 'description': 'Professional vocabulary'},
            {'id': 'daily_vocabulary', 'name': 'Daily Vocabulary', 'description': 'Everyday words'},
            {'id': 'technical_terms', 'name': 'Technical Terms', 'description': 'Science and technology words'}
        ],
        'sentence': [
            {'id': 'daily_conversation', 'name': 'Daily Conversation', 'description': 'Common daily phrases'},
            {'id': 'academic_discussion', 'name': 'Academic Discussion', 'description': 'Classroom and study phrases'},
            {'id': 'business_communication', 'name': 'Business Communication', 'description': 'Professional sentences'},
            {'id': 'exam_speaking', 'name': 'Exam Speaking', 'description': 'Test preparation sentences'},
            {'id': 'pronunciation_patterns', 'name': 'Pronunciation Patterns', 'description': 'Focus on specific sounds'},
            {'id': 'intonation_practice', 'name': 'Intonation Practice', 'description': 'Rhythm and stress patterns'}
        ],
        'paragraph': [
            {'id': 'self_introduction', 'name': 'Self Introduction', 'description': 'Introduce yourself'},
            {'id': 'topic_description', 'name': 'Topic Description', 'description': 'Describe various topics'},
            {'id': 'opinion_expression', 'name': 'Opinion Expression', 'description': 'Express your views'},
            {'id': 'academic_presentation', 'name': 'Academic Presentation', 'description': 'Present academic topics'},
            {'id': 'storytelling', 'name': 'Storytelling', 'description': 'Tell stories and experiences'},
            {'id': 'exam_response', 'name': 'Exam Response', 'description': 'TOEFL/IELTS speaking tasks'}
        ],
        'topic': [
            {'id': 'general', 'name': 'General Topics', 'description': 'Everyday life and common topics'},
            {'id': 'education', 'name': 'Education', 'description': 'School, learning, and academic topics'},
            {'id': 'technology', 'name': 'Technology', 'description': 'Computers, internet, and modern tech'},
            {'id': 'environment', 'name': 'Environment', 'description': 'Nature, climate, and sustainability'},
            {'id': 'culture', 'name': 'Culture & Society', 'description': 'Traditions, customs, and social issues'},
            {'id': 'work', 'name': 'Work & Career', 'description': 'Jobs, professions, and workplace topics'},
            {'id': 'travel', 'name': 'Travel & Places', 'description': 'Tourism, countries, and destinations'},
            {'id': 'health', 'name': 'Health & Lifestyle', 'description': 'Fitness, diet, and wellbeing'}
        ]
    }), 200