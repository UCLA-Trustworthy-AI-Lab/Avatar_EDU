from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.conversation_service import ConversationService
from app.api.openai_client import OpenAIClient
import json
import logging

bp = Blueprint('conversation', __name__, url_prefix='/api/conversation')

@bp.route('/chat', methods=['POST'])
@jwt_required()
def chat_with_avatar():
    """Handle conversation messages with AI avatar"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validate input
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
            
        message = data.get('message', '').strip()
        platform = data.get('platform', 'text')  # heygen, custom, text
        pronunciation_data = data.get('pronunciation_data')  # Optional pronunciation data from speech

        if not message:
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }), 400

        # Initialize conversation service
        conversation_service = ConversationService()

        # Process the conversation (with pronunciation data if from audio)
        response_data = conversation_service.process_conversation(
            user_id=user_id,
            message=message,
            platform=platform,
            pronunciation_data={'pronunciation_data': pronunciation_data} if pronunciation_data else None
        )
        
        return jsonify({
            'success': True,
            'response': response_data['response'],
            'audioUrl': response_data.get('audio_url'),
            'videoUrl': response_data.get('video_url'),
            'conversationId': response_data.get('conversation_id'),
            'analytics': response_data.get('analytics')
        })
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while processing your message'
        }), 500

@bp.route('/speech-to-text', methods=['POST'])
@jwt_required()
def speech_to_text():
    """Convert speech audio to text"""
    try:
        user_id = int(get_jwt_identity())
        
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided'
            }), 400
            
        audio_file = request.files['audio']
        
        # Initialize conversation service
        conversation_service = ConversationService()
        
        # Process speech to text with pronunciation assessment
        text_result = conversation_service.speech_to_text(audio_file, assess_pronunciation=True)

        return jsonify({
            'success': True,
            'text': text_result['text'],
            'confidence': text_result.get('confidence', 0.0),
            'pronunciation_data': text_result.get('pronunciation_data', {}),
            'has_pronunciation_feedback': bool(text_result.get('pronunciation_data'))
        })
        
    except Exception as e:
        logging.error(f"Speech-to-text error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to process audio'
        }), 500

@bp.route('/start-session', methods=['POST'])
@jwt_required()
def start_conversation_session():
    """Start a new conversation session"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        platform = data.get('platform', 'text')
        topic = data.get('topic', 'general_conversation')
        
        conversation_service = ConversationService()
        session_data = conversation_service.start_session(
            user_id=user_id,
            platform=platform,
            topic=topic
        )
        
        return jsonify({
            'success': True,
            'sessionId': session_data['session_id'],
            'welcomeMessage': session_data['welcome_message']
        })
        
    except Exception as e:
        logging.error(f"Start session error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to start conversation session'
        }), 500

@bp.route('/end-session', methods=['POST'])
@jwt_required()
def end_conversation_session():
    """End conversation session and get analytics"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        session_id = data.get('sessionId')
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'Session ID is required'
            }), 400
            
        conversation_service = ConversationService()
        analytics = conversation_service.end_session(user_id, session_id)
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'summary': analytics.get('session_summary'),
            'recommendations': analytics.get('recommendations')
        })
        
    except Exception as e:
        logging.error(f"End session error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to end conversation session'
        }), 500

@bp.route('/history', methods=['GET'])
@jwt_required()
def get_conversation_history():
    """Get user's conversation history"""
    try:
        user_id = int(get_jwt_identity())
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        conversation_service = ConversationService()
        history = conversation_service.get_user_history(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            'success': True,
            'conversations': history['conversations'],
            'total': history['total'],
            'hasMore': history['has_more']
        })
        
    except Exception as e:
        logging.error(f"Get history error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve conversation history'
        }), 500

# ===================
# STREAMING AVATAR CONVERSATION ENDPOINTS
# ===================

@bp.route('/streaming/start', methods=['POST'])
@jwt_required()
def start_streaming_conversation():
    """Start a streaming avatar conversation session"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        topic = data.get('topic', 'general')
        platform = data.get('platform', 'heygen')
        
        # Validate topic
        allowed_topics = ['general', 'daily_life', 'academic', 'business', 'travel']
        if topic not in allowed_topics:
            topic = 'general'
        
        conversation_service = ConversationService()
        session_result = conversation_service.start_streaming_conversation(
            user_id=user_id,
            topic=topic,
            platform=platform
        )
        
        if "error" in session_result:
            return jsonify({
                'success': False,
                'error': session_result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'sessionId': session_result['session_id'],
            'sessionKey': session_result['session_key'],
            'token': session_result['token'],
            'streamUrl': session_result.get('stream_url'),
            'sdp': session_result.get('sdp'),
            'iceServers': session_result.get('ice_servers'),
            'welcomeMessage': session_result['welcome_message'],
            'topic': session_result['topic'],
            'instructions': session_result['instructions']
        })
        
    except Exception as e:
        logging.error(f"Start streaming conversation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to start streaming conversation'
        }), 500

@bp.route('/streaming/message', methods=['POST'])
@jwt_required()
def process_streaming_message():
    """Process a message in streaming avatar conversation"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        session_key = data.get('sessionKey')
        user_message = data.get('message', '').strip()
        
        if not session_key:
            return jsonify({
                'success': False,
                'error': 'Session key is required'
            }), 400
            
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }), 400
        
        conversation_service = ConversationService()
        result = conversation_service.process_streaming_message(
            session_key=session_key,
            user_message=user_message
        )
        
        if "error" in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'userMessage': result['user_message'],
            'aiResponse': result['ai_response'],
            'taskId': result.get('task_id'),
            'pronunciationScore': result.get('pronunciation_score'),
            'conversationAnalysis': result.get('conversation_analysis'),
            'timestamp': result.get('timestamp')
        })
        
    except Exception as e:
        logging.error(f"Process streaming message error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to process streaming message'
        }), 500

@bp.route('/streaming/voice-message', methods=['POST'])
@jwt_required()
def process_streaming_voice_message():
    """Process a voice message in streaming avatar conversation"""
    try:
        user_id = int(get_jwt_identity())
        
        session_key = request.form.get('sessionKey')
        if not session_key:
            return jsonify({
                'success': False,
                'error': 'Session key is required'
            }), 400
        
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided'
            }), 400
            
        audio_file = request.files['audio']
        audio_data = audio_file.read()
        
        conversation_service = ConversationService()
        result = conversation_service.process_streaming_message(
            session_key=session_key,
            user_message="",  # Will be filled from audio transcription
            audio_data=audio_data
        )
        
        if "error" in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'userMessage': result['user_message'],
            'aiResponse': result['ai_response'],
            'taskId': result.get('task_id'),
            'pronunciationScore': result.get('pronunciation_score'),
            'conversationAnalysis': result.get('conversation_analysis'),
            'timestamp': result.get('timestamp')
        })
        
    except Exception as e:
        logging.error(f"Process streaming voice message error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to process voice message'
        }), 500

@bp.route('/streaming/stop', methods=['POST'])
@jwt_required()
def stop_streaming_conversation():
    """Stop streaming conversation and get detailed analytics"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        session_key = data.get('sessionKey')
        if not session_key:
            return jsonify({
                'success': False,
                'error': 'Session key is required'
            }), 400
        
        conversation_service = ConversationService()
        result = conversation_service.stop_streaming_conversation(session_key)
        
        if "error" in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'sessionStopped': result['session_stopped'],
            'analytics': result['analytics'],
            'status': result['status']
        })
        
    except Exception as e:
        logging.error(f"Stop streaming conversation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to stop streaming conversation'
        }), 500

@bp.route('/streaming/status/<session_key>', methods=['GET'])
@jwt_required()
def get_streaming_session_status(session_key):
    """Get current status of streaming session"""
    try:
        user_id = int(get_jwt_identity())
        
        conversation_service = ConversationService()
        status = conversation_service.get_streaming_session_status(session_key)
        
        if "error" in status:
            return jsonify({
                'success': False,
                'error': status['error']
            }), 404
        
        return jsonify({
            'success': True,
            'sessionInfo': status
        })
        
    except Exception as e:
        logging.error(f"Get streaming session status error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get session status'
        }), 500

@bp.route('/streaming/token', methods=['POST'])
@jwt_required()
def get_streaming_token():
    """Get HeyGen streaming token for frontend"""
    try:
        user_id = int(get_jwt_identity())
        
        conversation_service = ConversationService()
        token_result = conversation_service.heygen_client.create_streaming_token()
        
        if "error" in token_result:
            return jsonify({
                'success': False,
                'error': token_result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'token': token_result['token'],
            'expiresAt': token_result.get('expires_at')
        })
        
    except Exception as e:
        logging.error(f"Get streaming token error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get streaming token'
        }), 500

@bp.route('/reset', methods=['POST'])
@jwt_required()
def reset_conversation():
    """
    Reset/clear conversation context for the current user.
    Useful when you want to start fresh or if old context is cached.
    """
    try:
        user_id = int(get_jwt_identity())
        context_key = f"user_{user_id}"

        # Clear old conversation context (use class-level storage)
        if context_key in ConversationService._conversation_context:
            del ConversationService._conversation_context[context_key]
            logging.info(f"Cleared conversation context for user {user_id}")
            message = 'Conversation reset successfully. Your next message will load latest memory!'
        else:
            message = 'No active conversation found. Your next message will create a fresh conversation with latest memory!'

        return jsonify({
            'success': True,
            'message': message
        })

    except Exception as e:
        logging.error(f"Reset conversation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to reset conversation'
        }), 500

@bp.route('/memory-context', methods=['GET'])
@jwt_required()
def get_memory_context():
    """
    Get student's learning memory across all modules.
    This allows the avatar to reference vocabulary struggles, grammar patterns, etc.
    """
    try:
        user_id = int(get_jwt_identity())

        from app.services.memory_service import get_memory_service
        memory_service = get_memory_service()

        # Get memory from all modules
        reading_memory = memory_service.get_reading_memory(user_id)
        listening_memory = memory_service.get_listening_memory(user_id)
        speaking_memory = memory_service.get_speaking_memory(user_id)
        writing_memory = memory_service.get_writing_memory(user_id)
        conversation_memory = memory_service.get_conversation_memory(user_id)

        # Format for avatar consumption
        memory_context = {
            'reading': {
                'vocabulary_struggles': reading_memory.get('vocabulary_gaps', []),
                'comprehension_weaknesses': reading_memory.get('comprehension_weaknesses', []),
                'summary': reading_memory.get('summary', '')
            },
            'listening': {
                'comprehension_weaknesses': listening_memory.get('comprehension_weaknesses', []),
                'summary': listening_memory.get('summary', '')
            },
            'speaking': {
                'pronunciation_errors': speaking_memory.get('chronic_mispronunciations', []),
                'problem_phonemes': speaking_memory.get('problem_phonemes', []),
                'summary': speaking_memory.get('summary', '')
            },
            'writing': {
                'grammar_errors': writing_memory.get('chronic_grammar_errors', []),
                'style_issues': writing_memory.get('recurring_style_issues', []),
                'summary': writing_memory.get('summary', '')
            },
            'conversation': {
                'grammar_errors': conversation_memory.get('chronic_grammar_errors', []),
                'vocabulary_gaps': conversation_memory.get('vocabulary_gaps', []),
                'summary': conversation_memory.get('summary', '')
            }
        }

        return jsonify({
            'success': True,
            'memoryContext': memory_context
        })

    except Exception as e:
        logging.error(f"Get memory context error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve memory context'
        }), 500