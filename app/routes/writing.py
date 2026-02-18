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
                # Check if OpenAI returned an error (no API key, etc.)
                if isinstance(response, dict) and "error" in response:
                    raise ValueError(f"OpenAI unavailable: {response['error']}")

                # generate_content returns a dict, check if it's already parsed JSON
                if isinstance(response, dict) and "content" in response:
                    analysis_data = json.loads(response["content"])
                elif isinstance(response, dict):
                    analysis_data = response
                else:
                    analysis_data = json.loads(response)
            except (json.JSONDecodeError, TypeError):
                # Fallback analysis if JSON parsing fails
                analysis_data = _basic_text_analysis(text, topic, prompt)

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
            # Perform real basic text analysis instead of giving a fixed score
            fallback_analysis = _basic_text_analysis(text, topic, prompt)

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

def _basic_text_analysis(text: str, topic: str = '', prompt: str = '') -> dict:
    """
    Perform real basic text analysis without AI.
    Scores based on actual text quality metrics rather than giving a fixed score.
    """
    words = text.split()
    word_count = len(words)

    # Split into sentences (handle multiple punctuation types)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    sentence_count = len(sentences)

    # --- Word-level metrics ---
    unique_words = set(w.lower().strip('.,!?;:"\'-()[]') for w in words)
    unique_word_count = len(unique_words)
    avg_word_length = sum(len(w) for w in words) / max(word_count, 1)
    vocabulary_diversity = unique_word_count / max(word_count, 1)

    # Identify longer/advanced words (6+ letters)
    advanced_words = [w for w in unique_words if len(w) >= 6 and w.isalpha()]
    advanced_ratio = len(advanced_words) / max(unique_word_count, 1)

    # --- Sentence-level metrics ---
    sentence_lengths = [len(s.split()) for s in sentences]
    avg_sentence_length = sum(sentence_lengths) / max(sentence_count, 1)

    # Check sentence length variety (standard deviation)
    if len(sentence_lengths) > 1:
        mean_len = avg_sentence_length
        variance = sum((l - mean_len) ** 2 for l in sentence_lengths) / len(sentence_lengths)
        sentence_variety = variance ** 0.5
    else:
        sentence_variety = 0

    # --- Basic grammar checks ---
    grammar_issues = []

    # Check for sentences not starting with capital letter
    for i, s in enumerate(sentences):
        if s and not s[0].isupper():
            grammar_issues.append({
                "issue": "Capitalization",
                "sentence": s[:80],
                "correction": s[0].upper() + s[1:] if len(s) > 1 else s.upper(),
                "explanation": "Sentences should start with a capital letter"
            })

    # Check for very short sentences (fragments)
    for s in sentences:
        wc = len(s.split())
        if wc < 3 and wc > 0:
            grammar_issues.append({
                "issue": "Sentence fragment",
                "sentence": s,
                "correction": "Consider expanding this into a complete sentence",
                "explanation": "Very short sentences may be sentence fragments"
            })

    # Check for very long sentences (run-ons)
    for s in sentences:
        wc = len(s.split())
        if wc > 50:
            grammar_issues.append({
                "issue": "Run-on sentence",
                "sentence": s[:80] + "...",
                "correction": "Consider breaking this into shorter sentences",
                "explanation": "Sentences over 50 words are hard to follow"
            })

    # Check repeated words in succession
    for i in range(len(words) - 1):
        if words[i].lower().strip('.,!?') == words[i + 1].lower().strip('.,!?') and words[i].isalpha():
            grammar_issues.append({
                "issue": "Repeated word",
                "sentence": f"...{words[max(0,i-2):i+3]}...",
                "correction": f"Remove duplicate '{words[i]}'",
                "explanation": "Consecutive repeated words are usually unintentional"
            })

    # --- Topic relevance (basic keyword check) ---
    topic_words = set(w.lower() for w in (topic + ' ' + prompt).split() if len(w) > 3)
    text_words_lower = set(w.lower().strip('.,!?;:"\'-()[]') for w in words)
    topic_overlap = len(topic_words & text_words_lower) / max(len(topic_words), 1) if topic_words else 0.5
    on_topic = topic_overlap > 0.15

    # --- Scoring ---
    # Length score (0-25): penalize too short or too long
    if word_count < 50:
        length_score = max(5, word_count * 0.3)
    elif word_count < 100:
        length_score = 10 + (word_count - 50) * 0.2
    elif word_count < 250:
        length_score = 20
    elif word_count <= 500:
        length_score = 25
    else:
        length_score = 22  # Slightly penalize for being over limit

    # Vocabulary score (0-25)
    vocab_score = min(25, (vocabulary_diversity * 30) + (advanced_ratio * 40) + (avg_word_length - 3) * 3)
    vocab_score = max(5, vocab_score)

    # Structure score (0-25): sentence variety, avg length, paragraph structure
    structure_score = 10
    if 10 <= avg_sentence_length <= 25:
        structure_score += 8
    elif 8 <= avg_sentence_length <= 30:
        structure_score += 4
    if sentence_variety > 3:
        structure_score += 4
    if sentence_count >= 5:
        structure_score += 3
    structure_score = min(25, structure_score)

    # Grammar score (0-25): deduct for issues found
    grammar_score = max(5, 25 - len(grammar_issues) * 3)

    overall_score = int(length_score + vocab_score + structure_score + grammar_score)
    overall_score = max(10, min(100, overall_score))

    # --- Determine readability level ---
    if avg_word_length > 5.5 and vocabulary_diversity > 0.6:
        readability = "advanced"
    elif avg_word_length > 4.5 and vocabulary_diversity > 0.45:
        readability = "intermediate"
    else:
        readability = "basic"

    # --- Build strengths and weaknesses ---
    strengths = []
    areas_for_improvement = []

    if word_count >= 200:
        strengths.append("Good essay length")
    elif word_count < 100:
        areas_for_improvement.append(f"Essay is very short ({word_count} words). Aim for at least 250 words.")

    if vocabulary_diversity > 0.6:
        strengths.append("Good vocabulary diversity")
    else:
        areas_for_improvement.append("Try using more varied vocabulary instead of repeating words")

    if len(advanced_words) >= 5:
        strengths.append(f"Uses advanced vocabulary ({len(advanced_words)} complex words)")
    else:
        areas_for_improvement.append("Try incorporating more sophisticated vocabulary")

    if 10 <= avg_sentence_length <= 25:
        strengths.append("Good sentence length")
    elif avg_sentence_length < 8:
        areas_for_improvement.append("Sentences are too short. Try combining ideas.")
    elif avg_sentence_length > 30:
        areas_for_improvement.append("Sentences are too long. Break them into shorter ones.")

    if sentence_variety > 5:
        strengths.append("Good variety in sentence length")
    elif sentence_count > 3:
        areas_for_improvement.append("Vary your sentence lengths for better flow")

    if not grammar_issues:
        strengths.append("No obvious grammar issues detected")
    else:
        areas_for_improvement.append(f"Found {len(grammar_issues)} potential grammar issue(s)")

    if on_topic:
        strengths.append("Content appears relevant to the topic")
    else:
        areas_for_improvement.append("Essay may not address the given topic/prompt")

    if not strengths:
        strengths.append("Completed the writing task")
    if not areas_for_improvement:
        areas_for_improvement.append("Configure OpenAI API key in .env for detailed AI feedback")

    # --- Sentence-by-sentence basic analysis ---
    sentence_analysis = []
    for i, s in enumerate(sentences[:10]):  # Limit to first 10 sentences
        s_words = s.split()
        s_len = len(s_words)
        issues = []
        if s and not s[0].isupper():
            issues.append("Missing capitalization")
        if s_len < 3:
            issues.append("Very short - possible fragment")
        if s_len > 40:
            issues.append("Very long - consider splitting")

        effectiveness = "Strong" if 8 <= s_len <= 25 and not issues else "Adequate" if not issues else "Needs work"
        sentence_analysis.append({
            "sentence": s[:120],
            "issues": issues if issues else ["No obvious issues"],
            "alternatives": [],
            "score": max(3, min(10, 8 - len(issues)))
        })

    return {
        "overall_score": overall_score,
        "word_count": word_count,
        "readability_level": readability,
        "strengths": strengths,
        "areas_for_improvement": areas_for_improvement,
        "grammar_issues": grammar_issues[:10],  # Limit to 10
        "style_suggestions": [
            {
                "suggestion": "Vary sentence structure" if sentence_variety < 3 else "Maintain sentence variety",
                "example": f"Average sentence length: {avg_sentence_length:.1f} words",
                "priority": "high" if sentence_variety < 2 else "low"
            }
        ],
        "content_feedback": {
            "thesis_clarity": "unable to assess without AI",
            "argument_strength": "unable to assess without AI",
            "evidence_quality": "unable to assess without AI",
            "organization": "adequate" if sentence_count >= 5 else "needs more development",
            "conclusion_effectiveness": "unable to assess without AI"
        },
        "sentence_analysis": sentence_analysis,
        "vocabulary_assessment": {
            "complexity_level": readability,
            "advanced_words": sorted(list(advanced_words))[:15],
            "suggestions": areas_for_improvement[:2]
        },
        "overall_feedback": (
            f"Basic analysis: {word_count} words, {sentence_count} sentences, "
            f"vocabulary diversity {vocabulary_diversity:.0%}. "
            f"Score: {overall_score}/100. "
            f"Configure your OpenAI API key in .env for detailed AI-powered feedback "
            f"including grammar correction, style suggestions, and content analysis."
        ),
        "note": "This is a basic text analysis. For comprehensive AI-powered feedback, configure your OpenAI API key."
    }


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