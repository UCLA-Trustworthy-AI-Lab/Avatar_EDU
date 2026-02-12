from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.writing_service import WritingService
from app.api.openai_client import OpenAIClient
from datetime import datetime
import logging
import json
import re

logger = logging.getLogger(__name__)

bp = Blueprint('writing', __name__)

# Initialize services lazily to avoid application context issues
def get_writing_service():
    if not hasattr(get_writing_service, '_service'):
        get_writing_service._service = WritingService()
    return get_writing_service._service

def get_openai_client():
    if not hasattr(get_openai_client, '_client'):
        get_openai_client._client = OpenAIClient()
    return get_openai_client._client

def get_memory_service():
    if not hasattr(get_memory_service, '_service'):
        from app.services.memory_service import get_memory_service as get_svc
        get_memory_service._service = get_svc()
    return get_memory_service._service

@bp.route('/topics', methods=['GET'])
@jwt_required()
def get_writing_topics():
    """Get available writing topics organized by category"""
    try:
        topics = {
            "academic": [
                {
                    "id": 1,
                    "title": "Argumentative Essay",
                    "description": "Present and defend a position on a controversial topic",
                    "prompts": [
                        "Should social media platforms be regulated by governments?",
                        "Is online education as effective as traditional classroom learning?",
                        "Should universities require students to take courses outside their major?"
                    ]
                },
                {
                    "id": 2,
                    "title": "Research Analysis",
                    "description": "Analyze and synthesize information from multiple sources",
                    "prompts": [
                        "Analyze the impact of artificial intelligence on the job market",
                        "Compare different approaches to renewable energy adoption",
                        "Evaluate the effectiveness of different study techniques"
                    ]
                },
                {
                    "id": 3,
                    "title": "Literature Review",
                    "description": "Critically examine existing research on a topic",
                    "prompts": [
                        "Review recent studies on the effects of sleep on academic performance",
                        "Examine research on the relationship between exercise and mental health",
                        "Analyze studies on the effectiveness of language learning apps"
                    ]
                }
            ],
            "creative": [
                {
                    "id": 4,
                    "title": "Personal Narrative",
                    "description": "Share a meaningful personal experience",
                    "prompts": [
                        "Describe a moment when you had to step outside your comfort zone",
                        "Write about a time when you learned something important about yourself",
                        "Tell the story of a friendship that changed your perspective"
                    ]
                },
                {
                    "id": 5,
                    "title": "Descriptive Writing",
                    "description": "Paint a vivid picture with words",
                    "prompts": [
                        "Describe your ideal study environment in detail",
                        "Write about a place that holds special meaning for you",
                        "Describe a cultural festival or celebration from your hometown"
                    ]
                },
                {
                    "id": 6,
                    "title": "Opinion Piece",
                    "description": "Express your views on a topic that matters to you",
                    "prompts": [
                        "What is the most important skill students should learn in university?",
                        "How has technology changed the way people communicate?",
                        "What role should tradition play in modern society?"
                    ]
                }
            ],
            "business": [
                {
                    "id": 7,
                    "title": "Professional Email",
                    "description": "Practice formal business communication",
                    "prompts": [
                        "Write an email requesting a meeting with your professor",
                        "Compose a professional inquiry about an internship opportunity",
                        "Draft an email following up on a job application"
                    ]
                },
                {
                    "id": 8,
                    "title": "Proposal Writing",
                    "description": "Present ideas for projects or initiatives",
                    "prompts": [
                        "Propose a new student organization for your campus",
                        "Write a proposal for improving campus sustainability",
                        "Suggest a new course that should be added to your major"
                    ]
                },
                {
                    "id": 9,
                    "title": "Report Writing",
                    "description": "Present information in a structured, professional format",
                    "prompts": [
                        "Write a report on your internship experience",
                        "Analyze the results of a survey you conducted",
                        "Report on a campus event you organized or attended"
                    ]
                }
            ],
            "exam_prep": [
                {
                    "id": 10,
                    "title": "TOEFL Writing",
                    "description": "Practice integrated and independent writing tasks",
                    "prompts": [
                        "Do you agree or disagree: It is better to work in a team than alone?",
                        "Some people prefer to live in small towns, others in big cities. Which do you prefer?",
                        "Should governments spend more money on space exploration or solving problems on Earth?"
                    ]
                },
                {
                    "id": 11,
                    "title": "IELTS Writing Task 2",
                    "description": "Practice essay writing for IELTS Academic",
                    "prompts": [
                        "Some people think that universities should provide graduates with the knowledge and skills needed in the workplace. Others think that the true function of a university should be to give access to knowledge for its own sake. Discuss both views and give your opinion.",
                        "In many countries, the amount of crime is increasing. What do you think are the main causes of crime? How can we deal with those causes?",
                        "Some people believe that allowing children to make their own choices on everyday matters will result in a society of individuals who only think about their own wishes. Others believe that it is important for children to make decisions about matters that affect them. Discuss both views and give your opinion."
                    ]
                },
                {
                    "id": 12,
                    "title": "GRE Issue Essay",
                    "description": "Practice analytical writing for GRE",
                    "prompts": [
                        "The best way to teach is to praise positive actions and ignore negative ones.",
                        "In any field of endeavor, it is impossible to make a significant contribution without first being strongly influenced by past achievements within that field.",
                        "The most effective way to understand contemporary culture is to analyze the trends of its youth."
                    ]
                }
            ],
            "journal": [
                {
                    "id": 13,
                    "title": "Daily Reflection",
                    "description": "Reflect on your daily experiences and learning",
                    "prompts": [
                        "What was the most challenging part of your day and how did you handle it?",
                        "Describe something new you learned today and why it was interesting",
                        "What are you grateful for today and why?"
                    ]
                },
                {
                    "id": 14,
                    "title": "Goal Setting",
                    "description": "Plan and reflect on your goals",
                    "prompts": [
                        "What are your academic goals for this semester and how will you achieve them?",
                        "Describe a skill you want to develop and your plan for improvement",
                        "What career goals do you have and what steps are you taking to reach them?"
                    ]
                },
                {
                    "id": 15,
                    "title": "Cultural Comparison",
                    "description": "Compare and contrast different cultural perspectives",
                    "prompts": [
                        "Compare education systems in your home country and where you study now",
                        "How do work-life balance expectations differ between cultures you know?",
                        "Describe how communication styles vary between different cultures"
                    ]
                }
            ],
            "technical": [
                {
                    "id": 16,
                    "title": "Process Description",
                    "description": "Explain how something works or how to do something",
                    "prompts": [
                        "Explain how to prepare for an important exam",
                        "Describe the process of adapting to life in a new country",
                        "Explain how to effectively manage time as a student"
                    ]
                },
                {
                    "id": 17,
                    "title": "Problem-Solution Essay",
                    "description": "Identify problems and propose solutions",
                    "prompts": [
                        "What is the biggest challenge facing international students and how can it be addressed?",
                        "How can universities better support students' mental health?",
                        "What can be done to reduce academic stress among students?"
                    ]
                },
                {
                    "id": 18,
                    "title": "Instructions Writing",
                    "description": "Write clear, step-by-step instructions",
                    "prompts": [
                        "Write instructions for a new student on how to register for classes",
                        "Explain how to prepare for a job interview",
                        "Provide a guide for writing effective study notes"
                    ]
                }
            ]
        }

        return jsonify({
            'success': True,
            'topics': topics
        })

    except Exception as e:
        logger.error(f"Error getting writing topics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load writing topics'
        }), 500

@bp.route('/prompt', methods=['GET'])
@jwt_required()
def get_writing_prompt():
    """Get a specific writing prompt"""
    try:
        student_id = int(get_jwt_identity())

        topic = request.args.get('topic')
        if not topic:
            return jsonify({
                'success': False,
                'error': 'Topic is required'
            }), 400

        # Parse topic string to get category and topic info
        # Expected format: "category_topicId" or just topic name
        topic_id = 1  # default
        prompt_index = int(request.args.get('prompt_index', 0))

        # Get the specific prompt based on topic_id and prompt_index
        # This would typically come from a database

        # Create writing session
        writing_service = get_writing_service()
        session = writing_service.create_writing_session(student_id, f"topic_{topic}")

        # Generate prompt based on topic
        prompt_text = f"Write about {topic}. Focus on clear structure, strong arguments, and proper grammar."
        guidelines = [
            "Start with a clear introduction that states your main argument",
            "Use specific examples to support your points",
            "Organize your ideas in logical paragraphs",
            "End with a strong conclusion that reinforces your main points",
            "Check your grammar and spelling before submitting"
        ]

        # Customize based on topic type
        if "academic" in topic.lower():
            prompt_text = f"Write an academic essay about {topic}. Present a clear thesis and support it with evidence."
            guidelines.append("Use formal academic language and cite examples where appropriate")
        elif "creative" in topic.lower():
            prompt_text = f"Write a creative piece about {topic}. Let your imagination guide you while maintaining good structure."
            guidelines = ["Let your creativity flow", "Paint vivid pictures with your words", "Connect emotionally with your readers", "Use descriptive language", "Have a clear beginning, middle, and end"]
        elif "business" in topic.lower():
            prompt_text = f"Write a professional piece about {topic}. Use clear, concise language appropriate for a business context."
            guidelines.append("Use professional tone and business-appropriate language")

        # Mock prompt data - in production this would come from database
        prompt_data = {
            "session_id": session.id,
            "topic": topic,
            "prompt_index": prompt_index,
            "prompt": prompt_text,
            "guidelines": guidelines,
            "word_limit": {"min": 250, "max": 500},
            "time_limit": 45,  # minutes
            "difficulty": "intermediate"
        }

        return jsonify({
            'success': True,
            'prompt': prompt_data
        })

    except Exception as e:
        logger.error(f"Error getting writing prompt: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get writing prompt'
        }), 500

@bp.route('/analyze', methods=['POST'])
@jwt_required()
def analyze_writing():
    """Analyze submitted writing with GPT for grammar, style, and content"""
    try:
        student_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'Text is required for analysis'
            }), 400

        text = data['text']
        topic = data.get('topic', 'general writing')
        prompt = data.get('prompt', '')

        if len(text.strip()) < 50:
            return jsonify({
                'success': False,
                'error': 'Text is too short for meaningful analysis (minimum 50 characters)'
            }), 400

        try:
            # === LOAD MEMORY FOR ADAPTIVE FEEDBACK ===
            memory_service = get_memory_service()
            writing_memory = memory_service.get_writing_memory(student_id)
            memory_aware = bool(writing_memory)

            # Build memory context for personalized feedback
            memory_context = ""
            if memory_aware and writing_memory:
                chronic_grammar = writing_memory.get('chronic_grammar_errors', [])
                style_issues = writing_memory.get('recurring_style_issues', [])

                if chronic_grammar:
                    grammar_types = [e['error_type'] for e in chronic_grammar[:3]]
                    memory_context += f"\n🧠 STUDENT HISTORY - Known grammar weaknesses: {', '.join(grammar_types)}"
                    memory_context += "\n   → Pay special attention to these error types in your analysis"

                if style_issues:
                    style_types = [s['issue'] for s in style_issues[:3]]
                    memory_context += f"\n🧠 STUDENT HISTORY - Known style issues: {', '.join(style_types)}"
                    memory_context += "\n   → Check if these patterns appear in this essay"

                if writing_memory.get('summary'):
                    memory_context += f"\n🧠 OVERALL PATTERN: {writing_memory['summary']}"

            # Use OpenAI for comprehensive writing analysis
            openai_client = get_openai_client()

            analysis_prompt = f"""
You are an expert English writing teacher. Analyze this student essay and provide detailed feedback.

Topic: {topic}
Prompt: {prompt}

Student Essay:
{text}
{memory_context}

CRITICAL: You must respond with valid JSON only. Do not include any text before or after the JSON.

Return this exact JSON structure:
{{
    "overall_analysis": {{
        "score": (number 0-100),
        "summary": "Brief 2-3 sentence summary of the essay content",
        "on_topic": (true/false),
        "on_topic_explanation": "Does this essay address the given prompt?",
        "main_points": ["list", "of", "main", "arguments"],
        "thesis_statement": "Identified thesis or 'No clear thesis'",
        "conclusion_quality": "Assessment of conclusion strength"
    }},
    "grammar_analysis": {{
        "score": (number 0-100),
        "error_count": (number),
        "summary": "Brief grammar assessment",
        "common_errors": ["list", "of", "error", "types"],
        "specific_corrections": [
            {{
                "original": "exact text with error",
                "correction": "corrected version",
                "type": "error type",
                "explanation": "why this is wrong"
            }}
        ]
    }},
    "style_analysis": {{
        "score": (number 0-100),
        "tone": "description of writing tone",
        "vocabulary_level": "Basic/Intermediate/Advanced",
        "strengths": ["list", "of", "good", "aspects"],
        "suggestions": [
            {{
                "issue": "specific style issue",
                "example": "example from text",
                "improvement": "how to fix it"
            }}
        ]
    }},
    "sentence_by_sentence": [
        {{
            "sentence_number": 1,
            "original": "First sentence text",
            "analysis": {{
                "clarity": "Clear/Unclear/Confusing",
                "effectiveness": "Strong/Adequate/Weak",
                "issues": ["list", "of", "problems"],
                "suggestions": "how to improve",
                "alternative": "better version if needed"
            }}
        }}
    ],
    "recommendations": {{
        "top_priorities": ["priority 1", "priority 2", "priority 3"],
        "next_steps": "advice for next draft"
    }}
}}

Analyze every sentence individually. Be specific and constructive. Return only valid JSON."""

            response = openai_client.generate_content(
                analysis_prompt,
                max_tokens=2000,  # Increase for comprehensive analysis
                temperature=0.3   # Lower temperature for more consistent structure
            )

            # Parse the JSON response
            try:
                # generate_content returns a dict, check if it's already parsed JSON
                if isinstance(response, dict) and "content" in response:
                    analysis_data = json.loads(response["content"])
                elif isinstance(response, dict):
                    analysis_data = response
                else:
                    analysis_data = json.loads(response)
            except (json.JSONDecodeError, TypeError):
                # Fallback analysis if JSON parsing fails
                sentences = text.split('.')
                word_count = len(text.split())

                analysis_data = {
                    "overall_score": 75,
                    "word_count": word_count,
                    "readability_level": "intermediate",
                    "strengths": [
                        "Clear communication of ideas",
                        "Appropriate length for the task"
                    ],
                    "areas_for_improvement": [
                        "Consider adding more specific examples",
                        "Work on sentence variety"
                    ],
                    "grammar_issues": [
                        {
                            "issue": "Review needed",
                            "sentence": "Please review your writing for grammar accuracy",
                            "correction": "Use grammar checking tools for detailed feedback",
                            "explanation": "AI analysis temporarily unavailable"
                        }
                    ],
                    "style_suggestions": [
                        {
                            "suggestion": "Vary sentence structure",
                            "example": "Mix short and long sentences for better flow",
                            "priority": "medium"
                        }
                    ],
                    "content_feedback": {
                        "thesis_clarity": "adequate",
                        "argument_strength": "good",
                        "evidence_quality": "adequate",
                        "organization": "logical",
                        "conclusion_effectiveness": "adequate"
                    },
                    "sentence_analysis": [
                        {
                            "sentence": sentence.strip(),
                            "issues": ["Consider revising for clarity"],
                            "alternatives": ["Try rephrasing for better impact"],
                            "score": 7
                        } for sentence in sentences[:3] if sentence.strip()
                    ],
                    "vocabulary_assessment": {
                        "complexity_level": "intermediate",
                        "advanced_words": [],
                        "suggestions": ["Try incorporating more advanced vocabulary"]
                    },
                    "overall_feedback": "Your writing shows good organization and clear communication. Continue practicing to improve grammar and style."
                }

            # Update the writing session with analysis results
            session_id = data.get('session_id')
            if session_id:
                from app.models.session import LearningSession
                from app import db

                session = LearningSession.query.get(session_id)
                if session:
                    session.performance_score = analysis_data.get('overall_score', analysis_data.get('overall_analysis', {}).get('score', 0))
                    session.is_completed = True
                    session.completed_at = datetime.utcnow()
                    session.session_data = {
                        'text': text,
                        'topic': topic,
                        'prompt': prompt,
                        'analysis': analysis_data
                    }
                    db.session.commit()

                    # === MEMORY BOARD INTEGRATION ===
                    try:
                        # Extract insights from this session
                        insight = memory_service.extract_writing_session_insights(
                            student_id=student_id,
                            session_id=session_id,
                            analysis_data=analysis_data
                        )
                        logger.info(f"Extracted writing memory insights for session {session_id}")

                        # Check if compression is needed
                        if memory_service.should_compress_writing_memory(student_id):
                            compressed = memory_service.compress_writing_memory(
                                student_id=student_id,
                                use_ai=True
                            )
                            logger.info(f"Compressed writing memory for student {student_id}")

                    except Exception as e:
                        # Non-fatal: memory extraction failure shouldn't break the session
                        logger.error(f"Failed to extract/compress writing memory: {str(e)}")

            # === ENHANCE FEEDBACK WITH MEMORY-AWARE RECOMMENDATIONS ===
            if memory_aware and writing_memory:
                # Add memory-aware recommendations to the analysis
                memory_recommendations = []

                chronic_grammar = writing_memory.get('chronic_grammar_errors', [])
                if chronic_grammar:
                    top_grammar = chronic_grammar[0]['error_type']
                    memory_recommendations.append(
                        f"🧠 I remember you've been working on {top_grammar}. Keep practicing this area!"
                    )

                avg_score = writing_memory.get('average_score', 0)
                current_score = analysis_data.get('overall_score', analysis_data.get('overall_analysis', {}).get('score', 0))
                if avg_score and current_score > avg_score + 5:
                    memory_recommendations.append(
                        f"✨ Great progress! Your score improved from {avg_score:.1f} average to {current_score}"
                    )
                elif avg_score and current_score < avg_score - 5:
                    memory_recommendations.append(
                        f"📊 This score ({current_score}) is below your average ({avg_score:.1f}). Review the feedback carefully."
                    )

                # Add memory recommendations to the analysis
                if memory_recommendations:
                    if 'recommendations' not in analysis_data:
                        analysis_data['recommendations'] = {}

                    analysis_data['recommendations']['memory_insights'] = memory_recommendations

            return jsonify({
                'success': True,
                'analysis': analysis_data,
                'memory_aware': memory_aware
            })

        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")

            # Fallback analysis when OpenAI is not available
            sentences = text.split('.')
            word_count = len(text.split())

            fallback_analysis = {
                "overall_score": 70,
                "word_count": word_count,
                "readability_level": "intermediate",
                "strengths": [
                    "Completed the writing task",
                    "Appropriate length"
                ],
                "areas_for_improvement": [
                    "Use online grammar tools for detailed feedback",
                    "Consider peer review for content suggestions"
                ],
                "grammar_issues": [],
                "style_suggestions": [
                    {
                        "suggestion": "Review sentence structure",
                        "example": "Ensure sentences are clear and varied",
                        "priority": "medium"
                    }
                ],
                "content_feedback": {
                    "thesis_clarity": "adequate",
                    "argument_strength": "adequate",
                    "evidence_quality": "adequate",
                    "organization": "adequate",
                    "conclusion_effectiveness": "adequate"
                },
                "sentence_analysis": [],
                "vocabulary_assessment": {
                    "complexity_level": "basic",
                    "advanced_words": [],
                    "suggestions": ["Try using more sophisticated vocabulary"]
                },
                "overall_feedback": "Basic analysis completed. For detailed feedback, please ensure AI services are available."
            }

            return jsonify({
                'success': True,
                'analysis': fallback_analysis
            })

    except Exception as e:
        logger.error(f"Error analyzing writing: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to analyze writing'
        }), 500

@bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_writing_sessions():
    """Get writing session history for the current user"""
    try:
        student_id = int(get_jwt_identity())

        from app.models.session import LearningSession
        sessions = LearningSession.query.filter_by(
            student_id=student_id,
            module_type='writing'
        ).order_by(LearningSession.started_at.desc()).limit(10).all()

        session_data = []
        for session in sessions:
            session_data.append({
                'id': session.id,
                'started_at': session.started_at.isoformat() if session.started_at else None,
                'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                'performance_score': session.performance_score,
                'is_completed': session.is_completed,
                'activity_type': session.activity_type,
                'session_data': session.session_data
            })

        return jsonify({
            'success': True,
            'sessions': session_data
        })

    except Exception as e:
        logger.error(f"Error getting writing sessions: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get session history'
        }), 500

@bp.route('/save', methods=['POST'])
@jwt_required()
def save_draft():
    """Save a writing draft"""
    try:
        student_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'Text is required'
            }), 400

        # Save draft to session
        session_id = data.get('session_id')
        if session_id:
            from app.models.session import LearningSession
            session = LearningSession.query.get(session_id)
            if session and session.student_id == student_id:
                current_data = session.session_data or {}
                current_data.update({
                    'draft_text': data['text'],
                    'topic': data.get('topic'),
                    'prompt': data.get('prompt'),
                    'last_saved': datetime.utcnow().isoformat()
                })
                session.session_data = current_data
                from app import db
                db.session.commit()

                return jsonify({
                    'success': True,
                    'message': 'Draft saved successfully',
                    'saved_at': current_data['last_saved']
                })

        return jsonify({
            'success': False,
            'error': 'Invalid session'
        }), 400

    except Exception as e:
        logger.error(f"Error saving draft: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to save draft'
        }), 500