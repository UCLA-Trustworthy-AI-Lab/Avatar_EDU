from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.reading_service import ReadingService
from app.services.vocabulary_service import VocabularyService
from app.services.reading_chatbot_service import ReadingChatbotService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('reading', __name__)

# Initialize services lazily to avoid application context issues
def get_reading_service():
    if not hasattr(get_reading_service, '_service'):
        get_reading_service._service = ReadingService()
    return get_reading_service._service

def get_vocabulary_service():
    if not hasattr(get_vocabulary_service, '_service'):
        get_vocabulary_service._service = VocabularyService()
    return get_vocabulary_service._service

def get_chatbot_service():
    if not hasattr(get_chatbot_service, '_service'):
        get_chatbot_service._service = ReadingChatbotService()
    return get_chatbot_service._service

@bp.route('/materials/<int:material_id>', methods=['GET'])
@jwt_required()
def get_reading_material(material_id):
    """Get a specific reading material by ID"""
    try:
        student_id = int(get_jwt_identity())
        
        material = get_reading_service().get_material_by_id(material_id)
        
        if not material:
            return jsonify({
                'success': False,
                'error': 'Material not found'
            }), 404
            
        return jsonify({
            'success': True,
            'material': material
        })
        
    except Exception as e:
        logger.error(f"Error getting material {material_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch reading material'
        }), 500

@bp.route('/materials', methods=['GET'])
@jwt_required()
def get_reading_materials():
    """Get available reading materials for the current student"""
    try:
        student_id = int(get_jwt_identity())
        category = request.args.get('category')
        difficulty = request.args.get('difficulty')
        
        materials = get_reading_service().get_reading_materials_for_student(
            student_id=student_id,
            category=category,
            difficulty=difficulty
        )
        
        return jsonify({
            'success': True,
            'materials': materials,
            'total': len(materials)
        })
        
    except Exception as e:
        logger.error(f"Error getting reading materials: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch reading materials'
        }), 500

@bp.route('/session/start', methods=['POST'])
@jwt_required()
def start_reading_session():
    """Start a new interactive reading session"""
    try:
        student_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data or 'material_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Material ID is required'
            }), 400
        
        session_data = get_reading_service().create_interactive_reading_session(
            student_id=student_id,
            material_id=data['material_id']
        )
        
        if 'error' in session_data:
            return jsonify({
                'success': False,
                'error': session_data['error']
            }), 400
        
        return jsonify({
            'success': True,
            **session_data
        })
        
    except Exception as e:
        logger.error(f"Error starting reading session: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to start reading session'
        }), 500

@bp.route('/session/<int:session_id>/word-click', methods=['POST'])
@jwt_required()
def handle_word_click(session_id):
    """Handle word click during reading session"""
    try:
        student_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data or 'word' not in data:
            return jsonify({
                'success': False,
                'error': 'Word is required'
            }), 400
        
        include_chinese = data.get('include_chinese', False)
        
        word_data = get_reading_service().handle_word_click(
            student_id=student_id,
            reading_session_id=session_id,
            word=data['word'],
            include_chinese=include_chinese
        )
        
        if 'error' in word_data:
            return jsonify({
                'success': False,
                **word_data
            }), 400
        
        return jsonify({
            'success': True,
            'word_data': word_data
        })
        
    except Exception as e:
        logger.error(f"Error handling word click: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process word click'
        }), 500

@bp.route('/session/<int:session_id>/progress', methods=['PUT'])
@jwt_required()
def update_reading_progress(session_id):
    """Update reading progress in real-time"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Progress data is required'
            }), 400
        
        progress_data = get_reading_service().update_reading_progress_realtime(
            reading_session_id=session_id,
            progress_data=data
        )
        
        if 'error' in progress_data:
            return jsonify({
                'success': False,
                'error': progress_data['error']
            }), 400
        
        return jsonify({
            'success': True,
            'progress': progress_data
        })
        
    except Exception as e:
        logger.error(f"Error updating reading progress: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update progress'
        }), 500

@bp.route('/session/<int:session_id>/complete', methods=['POST'])
@jwt_required()
def complete_reading_session(session_id):
    """Complete a reading session and generate summary"""
    try:
        data = request.get_json() or {}
        
        completion_data = get_reading_service().complete_reading_session(
            reading_session_id=session_id,
            final_data=data
        )
        
        if 'error' in completion_data:
            return jsonify({
                'success': False,
                'error': completion_data['error']
            }), 400
        
        return jsonify({
            'success': True,
            **completion_data
        })
        
    except Exception as e:
        logger.error(f"Error completing reading session: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to complete session'
        }), 500

@bp.route('/vocabulary/stats', methods=['GET'])
@jwt_required()
def get_vocabulary_stats():
    """Get vocabulary learning statistics for the current student"""
    try:
        student_id = int(get_jwt_identity())
        
        stats = get_vocabulary_service().get_student_vocabulary_stats(student_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting vocabulary stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch vocabulary statistics'
        }), 500

@bp.route('/vocabulary/master', methods=['POST'])
@jwt_required()
def mark_word_mastered():
    """Mark a word as mastered by the student"""
    try:
        student_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data or 'word' not in data:
            return jsonify({
                'success': False,
                'error': 'Word is required'
            }), 400
        
        success = get_vocabulary_service().mark_word_as_mastered(
            student_id=student_id,
            word=data['word']
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to mark word as mastered'
            }), 500
        
        return jsonify({
            'success': True,
            'message': f"Word '{data['word']}' marked as mastered"
        })
        
    except Exception as e:
        logger.error(f"Error marking word as mastered: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process request'
        }), 500

@bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_reading_recommendations():
    """Get personalized reading recommendations"""
    try:
        student_id = int(get_jwt_identity())
        
        recommendations = get_reading_service().get_reading_recommendations(student_id)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        logger.error(f"Error getting reading recommendations: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get recommendations'
        }), 500

@bp.route('/materials/search', methods=['GET'])
@jwt_required()
def search_reading_materials():
    """Search reading materials by keywords, tags, or exam type"""
    try:
        student_id = int(get_jwt_identity())
        query = request.args.get('q', '').strip()
        exam_type = request.args.get('exam_type')
        tags = request.args.getlist('tags')
        
        # This would be implemented to search through materials
        # For now, return filtered materials
        materials = get_reading_service().get_reading_materials_for_student(student_id)
        
        # Simple filtering (in production, this would be done at the database level)
        if query:
            materials = [m for m in materials if query.lower() in m['title'].lower()]
        
        if exam_type:
            materials = [m for m in materials if exam_type in (m.get('target_exams') or [])]
        
        if tags:
            materials = [m for m in materials if any(tag in (m.get('tags') or []) for tag in tags)]
        
        return jsonify({
            'success': True,
            'materials': materials,
            'total': len(materials),
            'query': query,
            'filters': {
                'exam_type': exam_type,
                'tags': tags
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching reading materials: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to search materials'
        }), 500

@bp.route('/categories', methods=['GET'])
def get_reading_categories():
    """Get available reading categories"""
    try:
        categories = [
            {
                'id': 'academic',
                'name': 'Academic Papers',
                'description': 'Research papers and scholarly articles',
                'difficulty_levels': ['intermediate', 'advanced', 'expert']
            },
            {
                'id': 'news',
                'name': 'News Articles',
                'description': 'Current events and journalism',
                'difficulty_levels': ['beginner', 'intermediate', 'advanced']
            },
            {
                'id': 'literature',
                'name': 'Literature',
                'description': 'Classic and modern literary works',
                'difficulty_levels': ['intermediate', 'advanced', 'expert']
            },
            {
                'id': 'toefl',
                'name': 'TOEFL Preparation',
                'description': 'Reading passages similar to TOEFL exam',
                'difficulty_levels': ['intermediate', 'advanced']
            },
            {
                'id': 'ielts',
                'name': 'IELTS Preparation',
                'description': 'Reading passages similar to IELTS exam',
                'difficulty_levels': ['intermediate', 'advanced']
            },
            {
                'id': 'business',
                'name': 'Business English',
                'description': 'Professional and business contexts',
                'difficulty_levels': ['intermediate', 'advanced', 'expert']
            }
        ]
        
        return jsonify({
            'success': True,
            'categories': categories
        })
        
    except Exception as e:
        logger.error(f"Error getting reading categories: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch categories'
        }), 500

@bp.route('/difficulty-levels', methods=['GET'])
def get_difficulty_levels():
    """Get available difficulty levels"""
    try:
        levels = [
            {
                'id': 'beginner',
                'name': 'Beginner',
                'description': 'Basic vocabulary and simple sentence structures',
                'target_wpm': '150-200',
                'vocabulary_level': 'High school level'
            },
            {
                'id': 'intermediate',
                'name': 'Intermediate',
                'description': 'College-level vocabulary with moderate complexity',
                'target_wpm': '200-250',
                'vocabulary_level': 'College level'
            },
            {
                'id': 'advanced',
                'name': 'Advanced',
                'description': 'Academic vocabulary with complex structures',
                'target_wpm': '250-300',
                'vocabulary_level': 'Academic level'
            },
            {
                'id': 'expert',
                'name': 'Expert',
                'description': 'Professional and specialized vocabulary',
                'target_wpm': '300+',
                'vocabulary_level': 'Professional level'
            }
        ]
        
        return jsonify({
            'success': True,
            'levels': levels
        })
        
    except Exception as e:
        logger.error(f"Error getting difficulty levels: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch difficulty levels'
        }), 500

# Chatbot endpoints for reading assistance
@bp.route('/session/<int:session_id>/chatbot/ask', methods=['POST'])
@jwt_required()
def ask_chatbot(session_id):
    """Ask the AI chatbot a question about the current reading"""
    try:
        student_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        message_type = data.get('type', 'general')  # general, word_explanation, comprehension, reading_help
        
        response = get_chatbot_service().get_contextual_response(
            student_id=student_id,
            reading_session_id=session_id,
            user_message=data['message'],
            message_type=message_type
        )
        
        return jsonify({
            'success': True,
            'chatbot_response': response
        })
        
    except Exception as e:
        logger.error(f"Error in chatbot conversation: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get chatbot response'
        }), 500

@bp.route('/session/<int:session_id>/chatbot/explain-word', methods=['POST'])
@jwt_required()
def explain_word_in_context(session_id):
    """Get detailed explanation of a word in reading context"""
    try:
        student_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data or 'word' not in data:
            return jsonify({
                'success': False,
                'error': 'Word is required'
            }), 400
        
        response = get_chatbot_service().explain_word_in_context(
            student_id=student_id,
            reading_session_id=session_id,
            word=data['word'],
            sentence_context=data.get('sentence_context', '')
        )
        
        return jsonify({
            'success': True,
            'explanation': response
        })
        
    except Exception as e:
        logger.error(f"Error explaining word in context: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to explain word'
        }), 500

@bp.route('/session/<int:session_id>/chatbot/comprehension-help', methods=['POST'])
@jwt_required()
def get_comprehension_help(session_id):
    """Get help with reading comprehension questions"""
    try:
        student_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': 'Question is required'
            }), 400
        
        response = get_chatbot_service().get_reading_comprehension_help(
            student_id=student_id,
            reading_session_id=session_id,
            question=data['question']
        )
        
        return jsonify({
            'success': True,
            'help_response': response
        })
        
    except Exception as e:
        logger.error(f"Error providing comprehension help: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to provide comprehension help'
        }), 500

@bp.route('/session/<int:session_id>/chatbot/reading-tips', methods=['GET'])
@jwt_required()
def get_reading_tips(session_id):
    """Get personalized reading strategy tips"""
    try:
        student_id = int(get_jwt_identity())
        
        response = get_chatbot_service().get_reading_strategy_tips(
            student_id=student_id,
            reading_session_id=session_id
        )
        
        return jsonify({
            'success': True,
            'tips': response
        })
        
    except Exception as e:
        logger.error(f"Error getting reading tips: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get reading tips'
        }), 500

# Error handlers
@bp.route('/session/<int:session_id>/questions', methods=['POST'])
@jwt_required()
def generate_comprehension_questions(session_id):
    """Generate comprehension questions for Lock mode (with memory-based adaptation)"""
    try:
        student_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or 'text_content' not in data:
            return jsonify({
                'success': False,
                'error': 'Text content is required'
            }), 400

        text_content = data.get('text_content')
        num_questions = data.get('num_questions', 5)

        # Load student's memory to adapt questions
        from app.services.memory_service import get_memory_service
        memory_service = get_memory_service()
        adaptive_hints = memory_service.get_adaptive_question_focus(student_id)

        # Build adaptive instructions based on memory
        adaptive_instructions = ""
        if adaptive_hints.get('question_types_priority'):
            priority_types = adaptive_hints['question_types_priority'][:3]
            adaptive_instructions += f"\n- Prioritize these question types: {', '.join(priority_types)}"

        if adaptive_hints.get('challenge_words'):
            challenge_words = adaptive_hints['challenge_words'][:3]
            adaptive_instructions += f"\n- Include questions testing these vocabulary words the student struggled with: {', '.join(challenge_words)}"

        if adaptive_hints.get('memory_summary'):
            adaptive_instructions += f"\n- Student history: {adaptive_hints['memory_summary'][:150]}"

        # Use OpenAI to generate questions
        from app.api.openai_client import OpenAIClient
        openai_client = OpenAIClient()

        questions_prompt = f"""
        Create {num_questions} multiple choice comprehension questions based on this text for Chinese high school/college students (ages 16-20):

        TEXT:
        {text_content}

        Requirements:
        - Test understanding of main ideas, details, and inferences
        - Each question should have 4 options (A, B, C, D)
        - Questions should be appropriate for intermediate to advanced English learners
        - Include a mix of literal and inferential questions
        - Make sure only ONE option is clearly correct

        ADAPTIVE LEARNING (personalize to student's needs):{adaptive_instructions}

        Return as JSON array with this EXACT format:
        [
            {{
                "question": "What is the main idea of the passage?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "Option A"
            }}
        ]

        Return ONLY the JSON array, no other text.
        """
        
        response = openai_client.generate_content(questions_prompt, temperature=0.7)

        # Check if OpenAI is unavailable (no API key or error)
        if isinstance(response, dict) and 'error' in response:
            logger.warning(f"OpenAI unavailable: {response['error']}. Using fallback questions.")
            questions = _generate_fallback_questions(text_content, num_questions)
        elif isinstance(response, dict) and 'content' in response:
            import json
            try:
                questions = json.loads(response['content'])
            except json.JSONDecodeError:
                # Try to extract JSON from response
                content = response['content']
                start = content.find('[')
                end = content.rfind(']') + 1
                if start != -1 and end != 0:
                    questions = json.loads(content[start:end])
                else:
                    logger.warning("Could not parse AI response. Using fallback questions.")
                    questions = _generate_fallback_questions(text_content, num_questions)
        elif isinstance(response, list):
            questions = response
        else:
            logger.warning("Unexpected AI response format. Using fallback questions.")
            questions = _generate_fallback_questions(text_content, num_questions)
            
        # Validate questions format
        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError("AI did not return valid questions")
            
        for q in questions:
            if not all(key in q for key in ['question', 'options', 'correct_answer']):
                raise ValueError("Question format is invalid")
                
        return jsonify({
            'success': True,
            'questions': questions
        })
        
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate comprehension questions',
            'message': str(e)
        }), 500

@bp.route('/session/<int:session_id>/submit-answers', methods=['POST'])
@jwt_required()
def submit_comprehension_answers(session_id):
    """Submit and evaluate comprehension question answers"""
    try:
        student_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data or 'answers' not in data or 'questions' not in data:
            return jsonify({
                'success': False,
                'error': 'Answers and questions are required'
            }), 400
            
        answers = data.get('answers')
        questions = data.get('questions')
        
        # Calculate score
        correct_count = 0
        total_questions = len(questions)
        
        for i, question in enumerate(questions):
            user_answer = answers.get(str(i))
            if user_answer == question.get('correct_answer'):
                correct_count += 1
                
        score = round((correct_count / total_questions) * 100) if total_questions > 0 else 0
        
        # Generate feedback based on score
        if score >= 90:
            feedback = "Outstanding! You have excellent reading comprehension skills. Your understanding of both main ideas and details is impressive."
        elif score >= 80:
            feedback = "Great job! You demonstrated strong comprehension of the text. Keep up the excellent work with challenging materials."
        elif score >= 70:
            feedback = "Good work! You understood most of the text well. Focus on identifying key details and making inferences."
        elif score >= 60:
            feedback = "Not bad! You grasped the main ideas. Try reading more slowly and taking notes to improve detail comprehension."
        else:
            feedback = "Keep practicing! Focus on understanding main ideas first, then work on details. Consider reading shorter texts to build confidence."
            
        # Store results (you might want to save this to database)
        results = {
            'score': score,
            'correct_answers': correct_count,
            'total_questions': total_questions,
            'feedback': feedback,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error submitting answers: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to evaluate answers',
            'message': str(e)
        }), 500

def _generate_fallback_questions(text_content, num_questions=5):
    """Generate basic comprehension questions when OpenAI is unavailable"""
    import re

    sentences = [s.strip() for s in re.split(r'[.!?]+', text_content) if len(s.strip()) > 20]
    words = text_content.split()
    total_words = len(words)

    # Extract some key terms (longer words likely to be meaningful)
    key_words = sorted(set(w.strip('.,;:!?()[]"\'').lower() for w in words if len(w) > 6), key=lambda w: -len(w))[:10]

    questions = []

    # Question 1: Main idea
    questions.append({
        "question": "What is the main topic of this passage?",
        "options": [
            "The passage discusses " + (key_words[0] if key_words else "a specific topic") + " and related concepts",
            "The passage is primarily about cooking techniques",
            "The passage focuses on ancient history",
            "The passage is a fictional short story"
        ],
        "correct_answer": "The passage discusses " + (key_words[0] if key_words else "a specific topic") + " and related concepts"
    })

    # Question 2: Detail
    if len(sentences) > 1:
        questions.append({
            "question": "Based on the passage, which of the following details is mentioned?",
            "options": [
                sentences[0][:80] + "..." if len(sentences[0]) > 80 else sentences[0],
                "The author traveled to Antarctica for research",
                "The events took place in the 15th century",
                "The study involved only two participants"
            ],
            "correct_answer": sentences[0][:80] + "..." if len(sentences[0]) > 80 else sentences[0]
        })

    # Question 3: Vocabulary
    if len(key_words) >= 2:
        questions.append({
            "question": f"The word '{key_words[1]}' as used in the passage most likely relates to:",
            "options": [
                f"The main subject being discussed",
                "A type of musical instrument",
                "A geographical location",
                "A mathematical formula"
            ],
            "correct_answer": "The main subject being discussed"
        })

    # Question 4: Inference
    questions.append({
        "question": "What can be inferred about the author's purpose in writing this passage?",
        "options": [
            "To inform and educate the reader about the topic",
            "To persuade the reader to buy a product",
            "To entertain with a humorous anecdote",
            "To criticize a political figure"
        ],
        "correct_answer": "To inform and educate the reader about the topic"
    })

    # Question 5: Structure
    questions.append({
        "question": "How is the information in this passage primarily organized?",
        "options": [
            "By presenting ideas and supporting details",
            "By listing items in alphabetical order",
            "By comparing two opposing fictional characters",
            "By describing events in reverse chronological order"
        ],
        "correct_answer": "By presenting ideas and supporting details"
    })

    return questions[:num_questions]


# ============================================================================
# MEMORY BOARD ENDPOINTS - View student's learning patterns and adaptations
# ============================================================================

@bp.route('/memory-board', methods=['GET'])
@jwt_required()
def get_student_memory_board():
    """
    Get student's memory board - shows what the AI "remembers" about their learning patterns.
    Like a teacher's mental model of the student's strengths and weaknesses.
    """
    try:
        student_id = int(get_jwt_identity())

        from app.services.memory_service import get_memory_service
        memory_service = get_memory_service()

        # Get compressed reading memory
        reading_memory = memory_service.get_reading_memory(student_id)

        # Get adaptive hints (what would be used for next session)
        adaptive_hints = memory_service.get_adaptive_question_focus(student_id)

        return jsonify({
            'success': True,
            'memory_board': {
                'reading': reading_memory,
                'adaptive_hints': adaptive_hints
            }
        })

    except Exception as e:
        logger.error(f"Error fetching memory board: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch memory board'
        }), 500


@bp.route('/memory-board/compress', methods=['POST'])
@jwt_required()
def force_memory_compression():
    """
    Manually trigger memory compression (normally happens automatically).
    Useful for testing or if student wants to "update" their profile.
    """
    try:
        student_id = int(get_jwt_identity())

        from app.services.memory_service import get_memory_service
        memory_service = get_memory_service()

        # Force compression
        compressed = memory_service.compress_reading_memory(
            student_id=student_id,
            use_ai=True
        )

        return jsonify({
            'success': True,
            'compressed_memory': compressed,
            'message': 'Memory compression completed'
        })

    except Exception as e:
        logger.error(f"Error compressing memory: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to compress memory'
        }), 500


@bp.route('/memory-board/insights', methods=['GET'])
@jwt_required()
def get_reading_insights():
    """
    Get raw, uncompressed insights from recent reading sessions.
    Shows detailed breakdown of what happened in each session.
    """
    try:
        student_id = int(get_jwt_identity())

        from app.models.memory import ReadingMemoryInsight

        # Get last 5 insights (compressed and uncompressed)
        insights = ReadingMemoryInsight.query.filter_by(
            student_id=student_id
        ).order_by(ReadingMemoryInsight.created_at.desc()).limit(5).all()

        insights_data = []
        for insight in insights:
            insights_data.append({
                'session_id': insight.reading_session_id,
                'text_category': insight.text_category,
                'text_difficulty': insight.text_difficulty,
                'vocabulary_mistakes_count': len(insight.vocabulary_mistakes or []),
                'difficult_words_count': len(insight.difficult_words or []),
                'incorrect_questions_count': len(insight.incorrect_questions or []),
                'engagement_level': insight.engagement_level,
                'ai_summary': insight.ai_summary,
                'key_issues': insight.key_issues,
                'is_compressed': insight.is_compressed,
                'created_at': insight.created_at.isoformat()
            })

        return jsonify({
            'success': True,
            'recent_insights': insights_data,
            'total_count': len(insights_data)
        })

    except Exception as e:
        logger.error(f"Error getting reading insights: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch reading insights'
        }), 500


@bp.route('/memory-board/status', methods=['GET'])
@jwt_required()
def get_memory_status():
    """
    Diagnostic endpoint: Check memory system status and progress.
    Shows how many sessions completed and if compression is ready.
    """
    try:
        student_id = int(get_jwt_identity())

        from app.services.memory_service import get_memory_service
        from app.models.memory import ReadingMemoryInsight, StudentMemoryBoard

        memory_service = get_memory_service()

        # Count total insights
        total_insights = ReadingMemoryInsight.query.filter_by(
            student_id=student_id
        ).count()

        # Check if compressed memory exists
        memory_board = StudentMemoryBoard.query.filter_by(student_id=student_id).first()

        has_compressed_memory = False
        compressed_summary = None
        sessions_since_compression = 0

        if memory_board and memory_board.reading_memory:
            has_compressed_memory = True
            compressed_summary = memory_board.reading_memory.get('summary', 'No summary available')
            sessions_since_compression = memory_board.reading_sessions_since_compression or 0

        # Check if ready for compression
        ready_for_compression = memory_service.should_compress_reading_memory(student_id)

        # Get recent insights
        recent_insights = ReadingMemoryInsight.query.filter_by(
            student_id=student_id
        ).order_by(ReadingMemoryInsight.created_at.desc()).limit(3).all()

        recent_sessions = []
        for insight in recent_insights:
            recent_sessions.append({
                'session_id': insight.reading_session_id,
                'vocab_clicks': len(insight.vocabulary_mistakes or []),
                'questions_missed': len(insight.incorrect_questions or []),
                'created_at': insight.created_at.isoformat()
            })

        return jsonify({
            'success': True,
            'status': {
                'total_sessions_completed': total_insights,
                'sessions_since_last_compression': sessions_since_compression,
                'has_compressed_memory': has_compressed_memory,
                'ready_for_compression': ready_for_compression,
                'needs_more_sessions': total_insights < 5 and not has_compressed_memory,
                'sessions_needed': max(0, 5 - total_insights) if not has_compressed_memory else 0,
                'compressed_summary': compressed_summary[:200] if compressed_summary else None,
                'recent_sessions': recent_sessions
            },
            'message': _get_status_message(total_insights, has_compressed_memory, ready_for_compression)
        })

    except Exception as e:
        logger.error(f"Error getting memory status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get memory status'
        }), 500


def _get_status_message(total_insights, has_compressed_memory, ready_for_compression):
    """Generate helpful status message for students"""
    if total_insights == 0:
        return "No reading sessions completed yet. Complete your first session to start building memory!"

    if has_compressed_memory:
        return f"Memory system active! Avatar can access your reading history. You've completed {total_insights} sessions total."

    if ready_for_compression:
        return f"Ready for compression! You have {total_insights} sessions. Use POST /api/reading/memory-board/compress to compress now."

    sessions_needed = 5 - total_insights
    return f"Keep going! Complete {sessions_needed} more session(s) to activate memory compression (currently {total_insights}/5)."


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': str(error)
    }), 400

@bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Resource not found',
        'message': str(error)
    }), 404

@bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500