from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.listening_service import ListeningService
from app.api.azure_speech_client import AzureSpeechClient
from app.api.openai_client import OpenAIClient
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

bp = Blueprint('listening', __name__)

# Initialize services lazily to avoid application context issues
def get_listening_service():
    if not hasattr(get_listening_service, '_service'):
        get_listening_service._service = ListeningService()
    return get_listening_service._service

def get_azure_client():
    if not hasattr(get_azure_client, '_client'):
        get_azure_client._client = AzureSpeechClient()
    return get_azure_client._client

def get_openai_client():
    if not hasattr(get_openai_client, '_client'):
        get_openai_client._client = OpenAIClient()
    return get_openai_client._client

@bp.route('/topics', methods=['GET'])
@jwt_required()
def get_listening_topics():
    """Get available listening topics organized by category"""
    try:
        # Generate TOEFL topics dynamically from available audio files
        toefl_conversations = []
        toefl_lectures = []

        for i in range(1, 54):  # We have 53 TOEFL audio files
            file_num = str(i).zfill(4)
            if i % 2 == 1:  # Odd numbers are conversations
                conv_num = (i + 1) // 2
                toefl_conversations.append({
                    "id": i + 100,  # Offset to avoid conflicts
                    "title": f"TOEFL Conversation {conv_num}",
                    "description": "Campus conversation between students and staff",
                    "audio_file": f"toefl-listening-{file_num}-toefl-conversation-{conv_num}.mp3",
                    "transcript_file": f"toefl-listening-{file_num}-toefl-conversation-{conv_num}.txt"
                })
            else:  # Even numbers are lectures
                lec_num = i // 2
                toefl_lectures.append({
                    "id": i + 100,
                    "title": f"TOEFL Lecture {lec_num}",
                    "description": "Academic lecture on various subjects",
                    "audio_file": f"toefl-listening-{file_num}-toefl-lecture-{lec_num}.mp3",
                    "transcript_file": f"toefl-listening-{file_num}-toefl-lecture-{lec_num}.txt"
                })

        topics = {
            "toefl_conversations": toefl_conversations,
            "toefl_lectures": toefl_lectures,
            "daily_life": [
                {"id": 1, "title": "Morning Routine", "description": "Listen to someone describing their typical morning"},
                {"id": 2, "title": "Shopping Experience", "description": "A conversation at a grocery store"},
                {"id": 3, "title": "Weather Discussion", "description": "People talking about today's weather"}
            ],
            "academic": [
                {"id": 4, "title": "University Lecture", "description": "Introduction to Biology lecture excerpt"},
                {"id": 5, "title": "Study Groups", "description": "Students discussing their research project"},
                {"id": 6, "title": "Campus Life", "description": "International students sharing experiences"}
            ],
            "business": [
                {"id": 7, "title": "Job Interview", "description": "Professional interview conversation"},
                {"id": 8, "title": "Business Meeting", "description": "Team discussing quarterly goals"},
                {"id": 9, "title": "Workplace Communication", "description": "Colleagues collaborating on a project"}
            ],
            "travel": [
                {"id": 10, "title": "Airport Announcements", "description": "Flight information and boarding calls"},
                {"id": 11, "title": "Hotel Check-in", "description": "Guest checking into a hotel"},
                {"id": 12, "title": "Tourist Information", "description": "Asking for directions and recommendations"}
            ],
            "news": [
                {"id": 13, "title": "Technology News", "description": "Latest developments in AI and technology"},
                {"id": 14, "title": "Health & Wellness", "description": "Tips for maintaining good health"},
                {"id": 15, "title": "Environmental Issues", "description": "Climate change and conservation efforts"}
            ],
            "entertainment": [
                {"id": 16, "title": "Movie Reviews", "description": "Critics discussing recent films"},
                {"id": 17, "title": "Music Discussions", "description": "Musicians talking about their creative process"},
                {"id": 18, "title": "Sports Commentary", "description": "Analysis of recent sports events"}
            ]
        }

        return jsonify({
            'success': True,
            'topics': topics
        })

    except Exception as e:
        logger.error(f"Error getting listening topics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load listening topics'
        }), 500

@bp.route('/content/<int:topic_id>', methods=['GET'])
@jwt_required()
def get_listening_content(topic_id):
    """Get audio content and transcript for a specific topic"""
    try:
        student_id = int(get_jwt_identity())
        import os

        # Handle TOEFL content (IDs 101-153)
        if topic_id > 100:
            actual_id = topic_id - 100
            file_num = str(actual_id).zfill(4)

            if actual_id % 2 == 1:  # Conversation
                conv_num = (actual_id + 1) // 2
                audio_file = f"toefl-listening-{file_num}-toefl-conversation-{conv_num}.mp3"
                transcript_file = f"toefl-listening-{file_num}-toefl-conversation-{conv_num}.txt"
                title = f"TOEFL Conversation {conv_num}"
                category = "toefl_conversation"
            else:  # Lecture
                lec_num = actual_id // 2
                audio_file = f"toefl-listening-{file_num}-toefl-lecture-{lec_num}.mp3"
                transcript_file = f"toefl-listening-{file_num}-toefl-lecture-{lec_num}.txt"
                title = f"TOEFL Lecture {lec_num}"
                category = "toefl_lecture"

            # Read transcript
            transcript_path = os.path.join('data', 'transcripts', transcript_file)
            try:
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    transcript = f.read().strip()
            except FileNotFoundError:
                logger.warning(f"Transcript not found: {transcript_path}")
                transcript = "Transcript not available"

            content = {
                "title": title,
                "audio_url": f"/static/audio/{audio_file}",
                "transcript": transcript,
                "duration": 180,  # Approximate duration in seconds
                "difficulty": "advanced",
                "category": category
            }

            return jsonify({
                'success': True,
                'content': content
            })

        # Mock audio content for non-TOEFL topics
        content_data = {
            1: {
                "title": "Morning Routine",
                "audio_url": "/static/audio/morning_routine.mp3",
                "transcript": "Good morning! I usually wake up at 6:30 AM. The first thing I do is check my phone for any important messages, then I head to the bathroom to brush my teeth and wash my face. After that, I go to the kitchen to make coffee and prepare a simple breakfast, usually toast with jam or cereal with milk. While eating, I like to read the news on my tablet to stay updated with current events. Before leaving for work, I make sure to grab my keys, wallet, and lunch that I prepared the night before.",
                "duration": 45,
                "difficulty": "beginner",
                "category": "daily_life"
            },
            # Add more content as needed
        }

        if topic_id not in content_data:
            # Generate content using OpenAI for topics not pre-defined
            content = get_listening_service().generate_avatar_content(f"Topic {topic_id}", "intermediate")
            content_data[topic_id] = {
                "title": f"Topic {topic_id}",
                "audio_url": f"/static/audio/topic_{topic_id}.mp3",
                "transcript": content.get('story', 'Generated content not available'),
                "duration": 60,
                "difficulty": "intermediate",
                "category": "general"
            }

        content = content_data[topic_id]

        return jsonify({
            'success': True,
            'content': content
        })

    except Exception as e:
        logger.error(f"Error getting listening content for topic {topic_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load listening content'
        }), 500

@bp.route('/transcribe', methods=['POST'])
@jwt_required()
def transcribe_audio():
    """Transcribe audio using Azure Speech Services"""
    try:
        student_id = int(get_jwt_identity())

        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided'
            }), 400

        audio_file = request.files['audio']

        if audio_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Save audio file temporarily
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name

        try:
            # Use Azure Speech Services for transcription
            azure_client = get_azure_client()
            transcription = azure_client.speech_to_text(temp_path)

            return jsonify({
                'success': True,
                'transcription': transcription
            })

        except Exception as e:
            logger.error(f"Azure transcription failed: {e}")
            # Fallback mock transcription
            return jsonify({
                'success': True,
                'transcription': "This is a mock transcription since Azure services are not available."
            })

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Error in audio transcription: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to transcribe audio'
        }), 500

@bp.route('/questions', methods=['POST'])
@jwt_required()
def generate_questions():
    """Generate comprehension questions based on listening content"""
    try:
        student_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or 'transcript' not in data:
            return jsonify({
                'success': False,
                'error': 'Transcript is required'
            }), 400

        transcript = data['transcript']
        topic_id = data.get('topic_id')
        mode = data.get('mode', 'practice')  # 'practice' or 'test'

        # === LOAD MEMORY FOR ADAPTIVE QUESTIONS ===
        from app.services.memory_service import get_memory_service
        memory_service = get_memory_service()
        listening_memory = memory_service.get_listening_memory(student_id)

        # Build adaptive instructions based on memory
        adaptive_instructions = ""
        if listening_memory.get('comprehension_weaknesses'):
            weak_skills = [w.get('skill', '') for w in listening_memory['comprehension_weaknesses'][:3]]
            if weak_skills:
                adaptive_instructions += f"\n- PRIORITIZE these question types the student struggles with: {', '.join(weak_skills)}"

        if listening_memory.get('summary'):
            adaptive_instructions += f"\n- Student history: {listening_memory['summary'][:150]}"

        # === END MEMORY LOAD ===

        try:
            # Generate questions using OpenAI
            openai_client = get_openai_client()

            prompt = f"""
            Based on the following listening transcript, generate 5 comprehension questions suitable for English language learners.

            Transcript: {transcript}

            For each question, provide:
            1. The question text
            2. Four multiple choice options (A, B, C, D)
            3. The correct answer
            4. A brief explanation

            Make the questions test different skills:
            - Main idea comprehension
            - Detail recognition
            - Inference
            - Vocabulary in context
            - Sequence of events

            ADAPTIVE LEARNING (personalize to student's needs):{adaptive_instructions}

            Format as JSON with this structure:
            {{
                "questions": [
                    {{
                        "id": 1,
                        "question": "What is the main topic of the listening?",
                        "options": {{
                            "A": "Option A text",
                            "B": "Option B text",
                            "C": "Option C text",
                            "D": "Option D text"
                        }},
                        "correct_answer": "A",
                        "explanation": "Brief explanation of why A is correct"
                    }}
                ]
            }}
            """

            response = openai_client.generate_content(prompt)

            # Parse the JSON response
            try:
                if isinstance(response, dict) and "content" in response:
                    questions_data = json.loads(response["content"])
                elif isinstance(response, dict):
                    questions_data = response
                else:
                    questions_data = json.loads(response)
            except json.JSONDecodeError:
                # Fallback questions if JSON parsing fails
                questions_data = {
                    "questions": [
                        {
                            "id": 1,
                            "question": "What was the main topic of the listening passage?",
                            "options": {
                                "A": "Daily routine activities",
                                "B": "Travel experiences",
                                "C": "Business meetings",
                                "D": "Academic discussions"
                            },
                            "correct_answer": "A",
                            "explanation": "The passage focused on describing daily routine activities."
                        },
                        {
                            "id": 2,
                            "question": "According to the speaker, what time do they usually wake up?",
                            "options": {
                                "A": "6:00 AM",
                                "B": "6:30 AM",
                                "C": "7:00 AM",
                                "D": "7:30 AM"
                            },
                            "correct_answer": "B",
                            "explanation": "The speaker mentioned waking up at 6:30 AM."
                        }
                    ]
                }

            return jsonify({
                'success': True,
                'questions': questions_data['questions'],
                'mode': mode
            })

        except Exception as e:
            logger.error(f"OpenAI question generation failed: {e}")
            # Fallback questions
            fallback_questions = [
                {
                    "id": 1,
                    "question": "What was the main topic discussed in the audio?",
                    "options": {
                        "A": "Technology and innovation",
                        "B": "Daily life activities",
                        "C": "Travel experiences",
                        "D": "Business strategies"
                    },
                    "correct_answer": "B",
                    "explanation": "The audio primarily discussed daily life activities and routines."
                },
                {
                    "id": 2,
                    "question": "Which of the following was mentioned in the listening?",
                    "options": {
                        "A": "Morning exercise routine",
                        "B": "Cooking dinner",
                        "C": "Checking messages",
                        "D": "Evening entertainment"
                    },
                    "correct_answer": "C",
                    "explanation": "The speaker mentioned checking messages as part of their routine."
                }
            ]

            return jsonify({
                'success': True,
                'questions': fallback_questions,
                'mode': mode
            })

    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate questions'
        }), 500

@bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_answers():
    """Submit listening comprehension answers and get results"""
    try:
        student_id = int(get_jwt_identity())
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Request data is required'
            }), 400

        topic_id = data.get('topic_id')
        answers = data.get('answers', [])  # Array of answers
        questions = data.get('questions', [])  # Questions with correct answers
        mode = data.get('mode', 'practice')

        # Create or update listening session
        session = get_listening_service().create_listening_session(student_id, f"Topic {topic_id}")

        # Calculate score based on submitted answers
        correct_answers = 0
        total_questions = len(questions)
        detailed_results = []

        for i, question in enumerate(questions):
            student_answer = answers[i] if i < len(answers) else None
            is_correct = student_answer == question.get('correct_answer')

            if is_correct:
                correct_answers += 1

            detailed_results.append({
                'question': question.get('question'),
                'student_answer': student_answer,
                'correct_answer': question.get('correct_answer'),
                'is_correct': is_correct
            })

        score = (correct_answers / total_questions * 100) if total_questions > 0 else 0

        # Update session with results
        session.performance_score = score
        session.is_completed = True
        session.completed_at = datetime.utcnow()
        session.session_data = {
            'topic_id': topic_id,
            'mode': mode,
            'answers': answers,
            'questions': questions,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'detailed_results': detailed_results
        }

        from app import db
        db.session.commit()

        # === MEMORY BOARD INTEGRATION ===
        # Extract insights from this session (mistakes, patterns, challenges)
        from app.services.memory_service import get_memory_service
        memory_service = get_memory_service()

        try:
            # Extract insights
            insight = memory_service.extract_listening_session_insights(
                student_id=student_id,
                session_id=session.id
            )
            logger.info(f"Extracted listening memory insights for session {session.id}")

            # Check if we should compress memory
            if memory_service.should_compress_listening_memory(student_id):
                logger.info(f"Compressing listening memory for student {student_id}")
                compressed = memory_service.compress_listening_memory(
                    student_id=student_id,
                    use_ai=True
                )
                logger.info(f"Listening memory compression complete. Summary: {compressed.get('summary', 'N/A')[:100]}")

        except Exception as mem_error:
            logger.error(f"Listening memory tracking error (non-fatal): {mem_error}")
            # Don't fail the whole session if memory tracking fails

        # === END MEMORY BOARD INTEGRATION ===

        # Generate feedback
        feedback = {
            'score': score,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'performance_level': 'Excellent' if score >= 80 else 'Good' if score >= 60 else 'Needs Improvement',
            'recommendations': [
                "Practice listening to more TOEFL audio materials" if score < 70 else "Great job! Keep up the excellent work!",
                "Focus on identifying key details" if score < 60 else "Your comprehension is strong",
                "Review transcript for missed questions" if score < 80 else "You're ready for advanced materials"
            ],
            'detailed_results': detailed_results
        }

        return jsonify({
            'success': True,
            'session_id': session.id,
            'results': feedback
        })

    except Exception as e:
        logger.error(f"Error submitting listening answers: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to submit answers'
        }), 500

@bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_listening_sessions():
    """Get listening session history for the current user"""
    try:
        student_id = int(get_jwt_identity())

        from app.models.session import LearningSession
        sessions = LearningSession.query.filter_by(
            student_id=student_id,
            module_type='listening'
        ).order_by(LearningSession.started_at.desc()).limit(10).all()

        session_data = []
        for session in sessions:
            session_data.append({
                'id': session.id,
                'started_at': session.started_at.isoformat() if session.started_at else None,
                'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                'performance_score': session.performance_score,
                'is_completed': session.is_completed,
                'session_data': session.session_data
            })

        return jsonify({
            'success': True,
            'sessions': session_data
        })

    except Exception as e:
        logger.error(f"Error getting listening sessions: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get session history'
        }), 500