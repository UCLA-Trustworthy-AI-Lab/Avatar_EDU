import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from app.api.openai_client import OpenAIClient
from app.api.heygen_client import HeyGenClient
from app.api.azure_speech_client import AzureSpeechClient
import logging

class ConversationService:
    """Service for handling avatar conversations and analysis"""

    # Class-level storage (shared across all instances)
    _conversation_context = {}  # Persist across requests
    _streaming_sessions = {}  # Persist across requests

    def __init__(self):
        self.openai_client = OpenAIClient()
        self.heygen_client = HeyGenClient()
        self.azure_speech_client = AzureSpeechClient()
        # Use class-level storage instead of instance-level
        self.conversation_context = ConversationService._conversation_context
        self.streaming_sessions = ConversationService._streaming_sessions
        
    def process_conversation(self, user_id: int, message: str, platform: str = 'text', pronunciation_data: Dict = None) -> Dict[str, Any]:
        """
        Process a conversation message and generate AI response

        Args:
            user_id: User ID
            message: User's message
            platform: Platform type (heygen, custom, text)
            pronunciation_data: Optional pronunciation assessment data from audio

        Returns:
            Dictionary with response data
        """
        try:
            # Get or create conversation context
            context_key = f"user_{user_id}"
            if context_key not in self.conversation_context:
                self.conversation_context[context_key] = {
                    'messages': [],
                    'session_start': datetime.now(),
                    'platform': platform,
                    'topic': 'general_conversation',
                    'user_id': user_id,  # Add user_id for memory loading
                    'pronunciation_data': {  # Initialize pronunciation tracking
                        'mispronounced_words': [],
                        'phoneme_errors': [],
                        'scores': []
                    }
                }

            context = self.conversation_context[context_key]
            context['user_id'] = user_id  # Ensure user_id is always present

            # Store pronunciation data if provided (from audio conversations)
            if pronunciation_data and 'pronunciation_data' in context:
                pron_data = pronunciation_data.get('pronunciation_data', {})
                if pron_data:
                    context['pronunciation_data']['mispronounced_words'].extend(
                        pron_data.get('mispronounced_words', [])
                    )
                    context['pronunciation_data']['phoneme_errors'].extend(
                        pron_data.get('phoneme_errors', [])
                    )
                    if pron_data.get('scores'):
                        context['pronunciation_data']['scores'].append(pron_data['scores'])
            
            # Add user message to context
            context['messages'].append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Generate AI response
            ai_response = self._generate_ai_response(context, message)
            
            # Add AI response to context
            context['messages'].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Prepare response data
            response_data = {
                'response': ai_response,
                'conversation_id': context_key,
                'analytics': self._analyze_conversation_turn(message, ai_response)
            }
            
            # Add platform-specific features
            if platform == 'heygen':
                response_data['video_url'] = self._generate_heygen_video(ai_response)
            elif platform != 'text':
                response_data['audio_url'] = self._generate_speech_audio(ai_response)
                
            return response_data
            
        except Exception as e:
            logging.error(f"Conversation processing error: {str(e)}")
            return {
                'response': "I'm sorry, I'm having trouble understanding right now. Could you please try again?",
                'conversation_id': f"user_{user_id}",
                'analytics': {}
            }
    
    def _generate_ai_response(self, context: Dict, message: str) -> str:
        """Generate AI response using OpenAI with COMPLETE cross-module memory awareness"""
        try:
            # === LOAD ALL MODULE MEMORIES FOR COMPREHENSIVE PERSONALIZATION ===
            user_id = context.get('user_id')

            # DEBUG LOGGING
            logging.info(f"🔍 _generate_ai_response called")
            logging.info(f"🔍 user_id from context: {user_id}")
            logging.info(f"🔍 context keys: {context.keys()}")

            reading_memory = {}
            listening_memory = {}
            speaking_memory = {}
            writing_memory = {}
            conversation_memory = {}
            memory_aware = False

            if user_id:
                try:
                    from app.services.memory_service import get_memory_service
                    memory_service = get_memory_service()

                    # Load memories from ALL 5 modules
                    reading_memory = memory_service.get_reading_memory(user_id)
                    listening_memory = memory_service.get_listening_memory(user_id)
                    speaking_memory = memory_service.get_speaking_memory(user_id)
                    writing_memory = memory_service.get_writing_memory(user_id)
                    conversation_memory = memory_service.get_conversation_memory(user_id)

                    # DEBUG LOGGING
                    logging.info(f"🔍 Memory loading results:")
                    logging.info(f"   Reading: {'✅ HAS DATA' if reading_memory else '❌ EMPTY'}")
                    logging.info(f"   Listening: {'✅ HAS DATA' if listening_memory else '❌ EMPTY'}")
                    logging.info(f"   Speaking: {'✅ HAS DATA' if speaking_memory else '❌ EMPTY'}")
                    logging.info(f"   Writing: {'✅ HAS DATA' if writing_memory else '❌ EMPTY'}")
                    logging.info(f"   Conversation: {'✅ HAS DATA' if conversation_memory else '❌ EMPTY'}")

                    if reading_memory:
                        vocab_gaps = reading_memory.get('vocabulary_gaps', [])
                        logging.info(f"   📚 Reading vocab gaps: {[v['word'] for v in vocab_gaps[:3]]}")

                    memory_aware = any([reading_memory, listening_memory, speaking_memory,
                                       writing_memory, conversation_memory])
                    logging.info(f"🔍 memory_aware: {memory_aware}")
                except Exception as e:
                    logging.error(f"Failed to load module memories: {str(e)}")
                    import traceback
                    logging.error(traceback.format_exc())

            # Build comprehensive memory context for Avatar from ALL modules
            memory_context = ""
            if memory_aware:
                memory_context = "\n\n🧠 COMPLETE STUDENT HISTORY FROM ALL MODULES (YOU MUST USE THIS WHEN ASKED):"
                logging.info(f"✅ Memory is being loaded for user {user_id}")

                # === READING MODULE MEMORY ===
                if reading_memory:
                    vocab_gaps = reading_memory.get('vocabulary_gaps', [])
                    comp_weaknesses = reading_memory.get('comprehension_weaknesses', [])
                    chatbot_confusion = reading_memory.get('chatbot_topics_confused', [])

                    if vocab_gaps:
                        vocab_words = [v['word'] for v in vocab_gaps[:3]]
                        memory_context += f"\n📚 READING - Vocabulary struggles: {', '.join(vocab_words)}"
                        memory_context += "\n   → Use these words naturally in conversation and provide context"

                    if comp_weaknesses:
                        weakness_types = [w['skill'] for w in comp_weaknesses[:2]]
                        memory_context += f"\n📚 READING - Comprehension issues: {', '.join(weakness_types)}"
                        memory_context += "\n   → Practice these skills through conversation questions"

                    if chatbot_confusion:
                        confused_topics = [t['topic'] for t in chatbot_confusion[:2]]
                        memory_context += f"\n📚 READING - Confused about: {', '.join(confused_topics)}"
                        memory_context += "\n   → Clarify these concepts if they come up"

                # === LISTENING MODULE MEMORY ===
                if listening_memory:
                    comp_weaknesses = listening_memory.get('comprehension_weaknesses', [])

                    if comp_weaknesses:
                        weakness_types = [w['skill'] for w in comp_weaknesses[:2]]
                        memory_context += f"\n🎧 LISTENING - Comprehension issues: {', '.join(weakness_types)}"
                        memory_context += "\n   → Speak clearly and check understanding on these areas"

                # === SPEAKING MODULE MEMORY ===
                if speaking_memory:
                    chronic_mispron = speaking_memory.get('chronic_mispronunciations', [])
                    problem_phonemes = speaking_memory.get('problem_phonemes', [])

                    if chronic_mispron:
                        mispronounced = [w['word'] for w in chronic_mispron[:3]]
                        memory_context += f"\n🗣️ SPEAKING - Pronunciation issues: {', '.join(mispronounced)}"
                        memory_context += "\n   → Gently model correct pronunciation in responses"

                    if problem_phonemes:
                        phonemes = [p['phoneme'] for p in problem_phonemes[:2]]
                        memory_context += f"\n🗣️ SPEAKING - Problem sounds: {', '.join(phonemes)}"
                        memory_context += "\n   → Use words with these sounds for practice"

                # === WRITING MODULE MEMORY ===
                if writing_memory:
                    chronic_grammar = writing_memory.get('chronic_grammar_errors', [])
                    style_issues = writing_memory.get('recurring_style_issues', [])
                    vocab_issues = writing_memory.get('vocabulary_issues', [])

                    if chronic_grammar:
                        grammar_types = [e['error_type'] for e in chronic_grammar[:2]]
                        memory_context += f"\n✍️ WRITING - Grammar weaknesses: {', '.join(grammar_types)}"
                        memory_context += "\n   → Model correct grammar in conversation"

                    if style_issues:
                        style_types = [s['issue'] for s in style_issues[:2]]
                        memory_context += f"\n✍️ WRITING - Style issues: {', '.join(style_types)}"
                        memory_context += "\n   → Demonstrate proper style in responses"

                    if vocab_issues:
                        vocab_problems = [v['word'] for v in vocab_issues[:2]]
                        memory_context += f"\n✍️ WRITING - Vocabulary misuse: {', '.join(vocab_problems)}"
                        memory_context += "\n   → Use these words correctly in conversation as examples"

                # === CONVERSATION MODULE MEMORY ===
                if conversation_memory:
                    chronic_grammar = conversation_memory.get('chronic_grammar_errors', [])
                    vocab_gaps = conversation_memory.get('vocabulary_gaps', [])
                    fluency_patterns = conversation_memory.get('fluency_patterns', [])
                    chronic_mispronunciations = conversation_memory.get('chronic_mispronunciations', [])

                    if chronic_grammar:
                        grammar_types = [e['error_type'] for e in chronic_grammar[:2]]
                        memory_context += f"\n💬 CONVERSATION - Grammar patterns: {', '.join(grammar_types)}"
                        memory_context += "\n   → Gently correct when these errors appear"

                    if vocab_gaps:
                        gap_words = [v['word'] for v in vocab_gaps[:2]]
                        memory_context += f"\n💬 CONVERSATION - Vocabulary gaps: {', '.join(gap_words)}"
                        memory_context += "\n   → Practice these words in natural conversation"

                    if fluency_patterns:
                        fluency_issues = [f['issue'] for f in fluency_patterns[:2]]
                        memory_context += f"\n💬 CONVERSATION - Fluency issues: {', '.join(fluency_issues)}"
                        memory_context += "\n   → Encourage longer, more detailed responses"

                    if chronic_mispronunciations:
                        mispronounced = [w['word'] for w in chronic_mispronunciations[:2]]
                        memory_context += f"\n💬 CONVERSATION - Mispronunciations: {', '.join(mispronounced)}"
                        memory_context += "\n   → Gently model correct pronunciation"

                # Add overall summaries if available
                summaries = []
                if reading_memory.get('summary'):
                    summaries.append(f"Reading: {reading_memory['summary']}")
                if listening_memory.get('summary'):
                    summaries.append(f"Listening: {listening_memory['summary']}")
                if speaking_memory.get('summary'):
                    summaries.append(f"Speaking: {speaking_memory['summary']}")
                if writing_memory.get('summary'):
                    summaries.append(f"Writing: {writing_memory['summary']}")
                if conversation_memory.get('summary'):
                    summaries.append(f"Conversation: {conversation_memory['summary']}")

                if summaries:
                    memory_context += f"\n\n🧠 OVERALL PATTERNS:\n   " + "\n   ".join(summaries[:3])
            else:
                memory_context = "\n\n⚠️ NO LEARNING HISTORY AVAILABLE: This student hasn't completed any practice sessions yet. If they ask about their mistakes or struggles, politely tell them to complete some reading, speaking, or writing practice first so you can track their progress."
                logging.warning(f"⚠️ No memory available for user {user_id}")

            # DEBUGGING: Print the full memory context being sent to GPT
            logging.info(f"=" * 80)
            logging.info(f"🧠 MEMORY CONTEXT BEING SENT TO GPT:")
            logging.info(memory_context)
            logging.info(f"=" * 80)

            # Build conversation history for AI
            messages = [
                {
                    "role": "system",
                    "content": f"""You are an experienced English teacher helping Chinese students (aged 16-20) practice conversational English.

Your role:
- Be encouraging, patient, and supportive
- Help students build confidence in speaking English
- Correct mistakes gently and provide better alternatives
- Ask follow-up questions to keep the conversation flowing
- Adapt your language level to the student's proficiency
- Make conversations engaging and educational
- Focus on practical, real-world English usage

Guidelines:
- Keep responses conversational and natural (2-4 sentences)
- If students make mistakes, gently correct them: "Great! You could also say..."
- Ask questions to encourage more speaking practice
- Use examples from daily life, study, or interests
- Be culturally sensitive to Chinese students
- Encourage them to elaborate on their thoughts
- Provide pronunciation tips when helpful

🧠 CRITICAL INSTRUCTION - Student Memory Context:
I have loaded this student's complete learning history from the database. When they ask questions like:
- "What vocabulary did I struggle with?"
- "What mistakes did I make?"
- "Help me practice words I keep forgetting"

YOU MUST DIRECTLY REFERENCE THE SPECIFIC DATA BELOW. Do not say "I don't have that information" or redirect them.

EXAMPLE:
Student asks: "What vocabulary did I struggle with in reading?"
You respond: "Based on your reading sessions, you struggled with words like [LIST ACTUAL WORDS FROM DATA BELOW]. Let's practice using these words!"

DO NOT be vague. DO NOT avoid the question. USE THE ACTUAL DATA PROVIDED BELOW.
{memory_context}

Remember: The data below is REAL information from their learning sessions. Reference it directly when asked!"""
                }
            ]
            
            # Add recent conversation history (last 10 exchanges)
            recent_messages = context['messages'][-20:]  # Last 10 exchanges (user + assistant)
            for msg in recent_messages:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Generate response
            response = self.openai_client.generate_content(
                prompt="", 
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=200,
                temperature=0.8
            )
            
            # Extract response text
            if isinstance(response, dict) and 'content' in response:
                return response['content']
            elif isinstance(response, str):
                return response
            else:
                return "That's interesting! Could you tell me more about that?"
                
        except Exception as e:
            logging.error(f"AI response generation error: {str(e)}")
            return "I'd love to hear more about that! What do you think about it?"
    
    def _analyze_conversation_turn(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        """Analyze a single conversation turn for learning insights"""
        try:
            word_count = len(user_message.split())
            complexity_score = min(100, word_count * 5)  # Simple complexity metric
            
            # Basic engagement analysis
            question_words = ['what', 'where', 'when', 'why', 'how', 'who']
            has_question = any(word in user_message.lower() for word in question_words)
            
            return {
                'user_word_count': word_count,
                'complexity_score': complexity_score,
                'has_question': has_question,
                'message_length': len(user_message),
                'engagement_level': 'high' if word_count > 10 else 'medium' if word_count > 5 else 'low'
            }
        except:
            return {}
    
    def speech_to_text(self, audio_file, assess_pronunciation: bool = True) -> Dict[str, Any]:
        """
        Convert speech to text with pronunciation assessment

        Args:
            audio_file: Audio file object
            assess_pronunciation: Whether to assess pronunciation (default True)

        Returns:
            Dictionary with text, confidence, and pronunciation data
        """
        try:
            # Use Azure Speech Services for transcription + pronunciation
            result = self.azure_speech_client.recognize_speech_from_file(audio_file)

            pronunciation_data = {}

            if assess_pronunciation and result.get('text'):
                # Assess pronunciation using Azure
                pronunciation_result = self.azure_speech_client.assess_pronunciation(
                    audio_file,
                    reference_text=result.get('text', '')
                )

                if pronunciation_result and 'error' not in pronunciation_result:
                    # Extract mispronounced words
                    mispronounced_words = []
                    phoneme_errors = []

                    words = pronunciation_result.get('words', [])
                    for word in words:
                        accuracy = word.get('accuracy_score', 100)
                        if accuracy < 70:  # Low accuracy = mispronounced
                            mispronounced_words.append({
                                'word': word.get('word', ''),
                                'accuracy': accuracy
                            })

                        # Extract phoneme errors
                        for phoneme in word.get('phonemes', []):
                            if phoneme.get('accuracy_score', 100) < 60:
                                phoneme_errors.append({
                                    'phoneme': phoneme.get('phoneme', ''),
                                    'accuracy': phoneme.get('accuracy_score', 0)
                                })

                    pronunciation_data = {
                        'mispronounced_words': mispronounced_words,
                        'phoneme_errors': phoneme_errors,
                        'scores': {
                            'pronunciation': pronunciation_result.get('pronunciation_score', 0),
                            'accuracy': pronunciation_result.get('accuracy_score', 0),
                            'fluency': pronunciation_result.get('fluency_score', 0)
                        }
                    }

            return {
                'text': result.get('text', ''),
                'confidence': result.get('confidence', 0.0),
                'pronunciation_data': pronunciation_data
            }

        except Exception as e:
            logging.error(f"Speech-to-text error: {str(e)}")
            # Fallback to basic transcription without pronunciation
            return {
                'text': "",
                'confidence': 0.0,
                'pronunciation_data': {}
            }
    
    def _generate_speech_audio(self, text: str) -> Optional[str]:
        """
        Generate speech audio from text (placeholder)
        In production, this would integrate with text-to-speech service
        """
        try:
            # Placeholder - would return actual audio URL
            return f"/api/tts/audio/{uuid.uuid4()}.mp3"
        except:
            return None
    
    def _generate_heygen_video(self, text: str) -> Optional[str]:
        """
        Generate HeyGen avatar video (placeholder)
        In production, this would integrate with HeyGen's streaming API
        """
        try:
            # Placeholder - would return actual video stream URL
            return f"https://api.heygen.com/stream/{uuid.uuid4()}"
        except:
            return None
    
    def start_session(self, user_id: int, platform: str, topic: str) -> Dict[str, Any]:
        """Start a new conversation session with cross-module memory awareness"""
        try:
            context_key = f"user_{user_id}"
            session_id = str(uuid.uuid4())

            # Load ALL module memories to generate personalized welcome message
            welcome_message = None
            try:
                from app.services.memory_service import get_memory_service
                memory_service = get_memory_service()

                # Load all module memories
                reading_memory = memory_service.get_reading_memory(user_id)
                listening_memory = memory_service.get_listening_memory(user_id)
                speaking_memory = memory_service.get_speaking_memory(user_id)
                writing_memory = memory_service.get_writing_memory(user_id)
                conversation_memory = memory_service.get_conversation_memory(user_id)

                # Generate personalized welcome based on any module memory
                memory_hints = []

                if reading_memory:
                    vocab_gaps = reading_memory.get('vocabulary_gaps', [])
                    if vocab_gaps:
                        memory_hints.append(f"vocabulary like '{vocab_gaps[0]['word']}'")

                if speaking_memory:
                    chronic_mispron = speaking_memory.get('chronic_mispronunciations', [])
                    if chronic_mispron:
                        memory_hints.append(f"pronunciation of '{chronic_mispron[0]['word']}'")

                if writing_memory:
                    chronic_grammar = writing_memory.get('chronic_grammar_errors', [])
                    if chronic_grammar:
                        memory_hints.append(f"{chronic_grammar[0]['error_type']}")

                if conversation_memory:
                    chronic_grammar = conversation_memory.get('chronic_grammar_errors', [])
                    if chronic_grammar:
                        memory_hints.append(f"{chronic_grammar[0]['error_type']}")

                if memory_hints:
                    hint = memory_hints[0]
                    welcome_message = f"Welcome back! I remember we've been working on {hint}. Let's have a great conversation today!"

            except Exception as e:
                logging.error(f"Failed to load memory for welcome message: {str(e)}")

            # Initialize new session
            self.conversation_context[context_key] = {
                'session_id': session_id,
                'messages': [],
                'session_start': datetime.now(),
                'platform': platform,
                'topic': topic,
                'user_id': user_id
            }
            
            # Generate welcome message (use memory-aware if available)
            if not welcome_message:
                welcome_messages = {
                    'general_conversation': "Hello! I'm excited to have a conversation with you in English. What would you like to talk about today?",
                    'daily_life': "Hi there! Let's chat about daily life. How has your day been so far?",
                    'academic': "Welcome! I'm here to help you practice academic English. What subject are you studying?",
                    'business': "Hello! Let's practice business English together. Are you interested in any particular industry?"
                }

                welcome_message = welcome_messages.get(topic, welcome_messages['general_conversation'])
            
            return {
                'session_id': session_id,
                'welcome_message': welcome_message
            }
            
        except Exception as e:
            logging.error(f"Start session error: {str(e)}")
            return {
                'session_id': str(uuid.uuid4()),
                'welcome_message': "Hello! Let's have a great conversation in English!"
            }
    
    def end_session(self, user_id: int, session_id: str) -> Dict[str, Any]:
        """End conversation session and provide analytics"""
        try:
            context_key = f"user_{user_id}"
            
            if context_key not in self.conversation_context:
                return {'error': 'Session not found'}
            
            context = self.conversation_context[context_key]
            
            # Calculate session analytics
            total_messages = len([msg for msg in context['messages'] if msg['role'] == 'user'])
            total_words = sum(len(msg['content'].split()) for msg in context['messages'] if msg['role'] == 'user')
            session_duration = (datetime.now() - context['session_start']).total_seconds() / 60  # minutes
            
            analytics = {
                'total_exchanges': total_messages,
                'total_words_spoken': total_words,
                'session_duration_minutes': round(session_duration, 1),
                'average_words_per_message': round(total_words / max(total_messages, 1), 1),
                'fluency_score': min(100, total_words * 2),  # Simple scoring
                'engagement_score': min(100, total_messages * 10),
                'session_summary': f"Great conversation! You spoke {total_words} words across {total_messages} messages.",
                'recommendations': [
                    "Continue practicing daily conversations to build fluency",
                    "Try discussing different topics to expand vocabulary",
                    "Focus on asking more questions to improve interaction skills"
                ]
            }

            # === MEMORY BOARD INTEGRATION ===
            try:
                from app.services.memory_service import get_memory_service
                memory_service = get_memory_service()

                # Build session data for memory extraction
                session_data = {
                    'messages': context['messages'],
                    'analytics': analytics,
                    'topic': context.get('topic', 'general_conversation'),
                    'platform': context.get('platform', 'text'),
                    'pronunciation_data': context.get('pronunciation_data', {})
                }

                # Extract insights from this conversation
                insight = memory_service.extract_conversation_session_insights(
                    student_id=user_id,
                    session_data=session_data
                )
                logging.info(f"Extracted conversation memory insights for student {user_id}")

                # Check if compression is needed
                if memory_service.should_compress_conversation_memory(user_id):
                    compressed = memory_service.compress_conversation_memory(
                        student_id=user_id,
                        use_ai=True
                    )
                    logging.info(f"Compressed conversation memory for student {user_id}")

            except Exception as e:
                # Non-fatal: memory extraction failure shouldn't break the session
                logging.error(f"Failed to extract/compress conversation memory: {str(e)}")

            # Clear session
            del self.conversation_context[context_key]

            return analytics
            
        except Exception as e:
            logging.error(f"End session error: {str(e)}")
            return {'error': 'Failed to end session'}
    
    def get_user_history(self, user_id: int, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """Get user's conversation history (placeholder)"""
        try:
            # Placeholder implementation
            # In production, this would query the database
            return {
                'conversations': [],
                'total': 0,
                'has_more': False
            }
        except Exception as e:
            logging.error(f"Get history error: {str(e)}")
            return {
                'conversations': [],
                'total': 0,
                'has_more': False
            }
    
    # ===================
    # STREAMING AVATAR CONVERSATION METHODS
    # ===================
    
    def start_streaming_conversation(self, user_id: int, topic: str = "general", platform: str = "heygen") -> Dict[str, Any]:
        """Start a streaming avatar conversation session"""
        try:
            # Create HeyGen streaming session
            session_result = self.heygen_client.create_conversation_session(user_id, topic)
            
            if "error" in session_result:
                return session_result
            
            # Store session info
            session_key = f"user_{user_id}_{session_result['session_id']}"
            self.streaming_sessions[session_key] = {
                'session_id': session_result['session_id'],
                'user_id': user_id,
                'topic': topic,
                'platform': platform,
                'started_at': datetime.now(),
                'messages': [],
                'analytics': {
                    'total_turns': 0,
                    'total_words': 0,
                    'average_response_time': 0,
                    'engagement_scores': []
                }
            }
            
            # Also create regular conversation context for analysis
            context_key = f"user_{user_id}"
            self.conversation_context[context_key] = {
                'messages': [],
                'session_start': datetime.now(),
                'platform': 'heygen_streaming',
                'topic': topic,
                'streaming_session_id': session_result['session_id']
            }
            
            return {
                **session_result,
                'session_key': session_key,
                'instructions': {
                    'speak_clearly': 'Speak clearly and at a natural pace',
                    'topic_focus': f'We\'ll be discussing: {topic}',
                    'encouragement': 'Remember, this is practice - making mistakes is part of learning!'
                }
            }
            
        except Exception as e:
            logging.error(f"Start streaming conversation error: {str(e)}")
            return {"error": f"Failed to start streaming conversation: {str(e)}"}
    
    def process_streaming_message(self, session_key: str, user_message: str, audio_data: bytes = None) -> Dict[str, Any]:
        """Process a message in streaming avatar conversation"""
        try:
            if session_key not in self.streaming_sessions:
                return {"error": "Session not found"}
            
            session = self.streaming_sessions[session_key]
            session_id = session['session_id']
            user_id = session['user_id']
            
            # Transcribe audio if provided
            if audio_data:
                transcription_result = self.azure_speech_client.speech_to_text(audio_data)
                if transcription_result.get('success'):
                    user_message = transcription_result.get('text', user_message)
                    pronunciation_score = transcription_result.get('pronunciation_score', 0)
                else:
                    return {"error": "Speech transcription failed"}
            else:
                pronunciation_score = None
            
            # Generate AI response using OpenAI
            ai_response = self._generate_enhanced_ai_response(user_message, session)
            
            # Send response to HeyGen streaming avatar
            heygen_result = self.heygen_client.handle_conversation_turn(
                session_id, 
                ai_response,
                {"user_message": user_message, "user_id": user_id}
            )
            
            if "error" in heygen_result:
                return heygen_result
            
            # Record conversation turn
            turn_data = {
                'user_message': user_message,
                'ai_response': ai_response,
                'timestamp': datetime.now().isoformat(),
                'pronunciation_score': pronunciation_score,
                'analysis': heygen_result.get('conversation_analysis', {})
            }
            
            session['messages'].append(turn_data)
            session['analytics']['total_turns'] += 1
            session['analytics']['total_words'] += len(user_message.split())
            
            # Update conversation context for continuity
            context_key = f"user_{user_id}"
            if context_key in self.conversation_context:
                context = self.conversation_context[context_key]
                context['messages'].extend([
                    {'role': 'user', 'content': user_message, 'timestamp': datetime.now().isoformat()},
                    {'role': 'assistant', 'content': ai_response, 'timestamp': datetime.now().isoformat()}
                ])
            
            return {
                'user_message': user_message,
                'ai_response': ai_response,
                'task_id': heygen_result.get('task_id'),
                'pronunciation_score': pronunciation_score,
                'conversation_analysis': heygen_result.get('conversation_analysis', {}),
                'status': 'success'
            }
            
        except Exception as e:
            logging.error(f"Process streaming message error: {str(e)}")
            return {"error": f"Failed to process streaming message: {str(e)}"}
    
    def _generate_enhanced_ai_response(self, user_message: str, session: Dict) -> str:
        """Generate enhanced AI response for streaming conversation with FULL MEMORY AWARENESS"""
        try:
            # === LOAD ALL MODULE MEMORIES FOR COMPREHENSIVE PERSONALIZATION ===
            user_id = session.get('user_id')

            reading_memory = {}
            listening_memory = {}
            speaking_memory = {}
            writing_memory = {}
            conversation_memory = {}
            memory_aware = False

            if user_id:
                try:
                    from app.services.memory_service import get_memory_service
                    memory_service = get_memory_service()

                    # Load memories from ALL 5 modules
                    reading_memory = memory_service.get_reading_memory(user_id)
                    listening_memory = memory_service.get_listening_memory(user_id)
                    speaking_memory = memory_service.get_speaking_memory(user_id)
                    writing_memory = memory_service.get_writing_memory(user_id)
                    conversation_memory = memory_service.get_conversation_memory(user_id)

                    memory_aware = any([reading_memory, listening_memory, speaking_memory,
                                       writing_memory, conversation_memory])
                    logging.info(f"✅ Streaming conversation memory loaded for user {user_id}: {memory_aware}")
                except Exception as e:
                    logging.error(f"Failed to load module memories in streaming: {str(e)}")

            # Build comprehensive memory context from ALL modules
            memory_context = ""
            if memory_aware:
                memory_context = "\n\n🧠 COMPLETE STUDENT HISTORY (USE THIS DATA WHEN ASKED):"

                # Reading memory
                if reading_memory:
                    vocab_gaps = reading_memory.get('vocabulary_gaps', [])
                    if vocab_gaps:
                        vocab_words = [v['word'] for v in vocab_gaps[:3]]
                        memory_context += f"\n📚 READING - Vocabulary struggles: {', '.join(vocab_words)}"

                # Speaking memory
                if speaking_memory:
                    chronic_mispron = speaking_memory.get('chronic_pronunciation_errors', [])
                    if chronic_mispron:
                        mispronounced = [w['word'] for w in chronic_mispron[:3]]
                        memory_context += f"\n🗣️ SPEAKING - Pronunciation issues: {', '.join(mispronounced)}"

                # Writing memory
                if writing_memory:
                    grammar_errors = writing_memory.get('chronic_grammar_errors', [])
                    if grammar_errors:
                        grammar_types = [e['error_type'] for e in grammar_errors[:2]]
                        memory_context += f"\n✍️ WRITING - Grammar weaknesses: {', '.join(grammar_types)}"

            # Build context from session
            topic = session.get('topic', 'general')
            recent_messages = session.get('messages', [])[-10:]  # Last 5 exchanges

            # Create enhanced system prompt with memory
            system_prompt = f"""You are an experienced, encouraging English teacher having a streaming video conversation with a Chinese student (aged 16-20) through an AI avatar.

CONVERSATION TOPIC: {topic}

Your role:
- Be warm, encouraging, and supportive like a caring teacher
- Help students build confidence in speaking English naturally
- Gently correct mistakes and provide better alternatives
- Ask follow-up questions to keep conversation flowing
- Adapt your language level to match the student's proficiency
- Make conversations engaging, educational, and confidence-building
- Focus on practical, real-world English usage
- Be culturally sensitive and understanding

Response Guidelines:
- Keep responses conversational and natural (2-4 sentences maximum)
- If students make mistakes, gently correct: "Great! You could also say..."
- Ask engaging questions to encourage more speaking
- Use examples from daily life, studies, or interests relevant to topic
- Provide gentle pronunciation tips when helpful: "Try emphasizing the first syllable"
- Show genuine interest in their thoughts and experiences
- Encourage elaboration: "That's interesting! Can you tell me more?"

🧠 CRITICAL INSTRUCTION - Student Memory Context:
When the student asks questions like "What vocabulary did I struggle with?" or "What mistakes did I make?" or "Help me practice words I keep forgetting", YOU MUST DIRECTLY REFERENCE THE SPECIFIC DATA BELOW. Do not say "I don't have that information" or redirect them.

EXAMPLE:
Student asks: "What vocabulary did I struggle with in reading?"
You respond: "Based on your reading sessions, you struggled with words like [LIST ACTUAL WORDS FROM DATA BELOW]. Let's practice using these words!"

DO NOT be vague. USE THE ACTUAL DATA PROVIDED BELOW.
{memory_context}

Remember: This is a live video conversation - be natural, warm, and encouraging while using their learning history!"""

            messages = [{"role": "system", "content": system_prompt}]
            
            # Add recent conversation history
            for msg_data in recent_messages:
                messages.extend([
                    {"role": "user", "content": msg_data['user_message']},
                    {"role": "assistant", "content": msg_data['ai_response']}
                ])
            
            # Add current message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = self.openai_client.generate_content(
                prompt="",
                model="gpt-4",
                messages=messages,
                max_tokens=150,
                temperature=0.8
            )
            
            if isinstance(response, dict) and 'content' in response:
                return response['content']
            elif isinstance(response, str):
                return response
            else:
                return "That's really interesting! Could you tell me more about that?"
                
        except Exception as e:
            logging.error(f"Enhanced AI response generation error: {str(e)}")
            return "I'd love to hear more about that! What do you think?"
    
    def stop_streaming_conversation(self, session_key: str) -> Dict[str, Any]:
        """Stop streaming conversation and provide detailed analytics"""
        try:
            if session_key not in self.streaming_sessions:
                return {"error": "Session not found"}
            
            session = self.streaming_sessions[session_key]
            session_id = session['session_id']
            user_id = session['user_id']
            
            # Stop HeyGen streaming session
            heygen_result = self.heygen_client.stop_streaming_session(session_id)
            
            # Calculate comprehensive analytics
            analytics = self._calculate_streaming_analytics(session)
            
            # Clean up session
            del self.streaming_sessions[session_key]
            
            # Clean up conversation context
            context_key = f"user_{user_id}"
            if context_key in self.conversation_context:
                del self.conversation_context[context_key]
            
            return {
                'session_stopped': heygen_result.get('status') == 'stopped',
                'analytics': analytics,
                'status': 'completed'
            }
            
        except Exception as e:
            logging.error(f"Stop streaming conversation error: {str(e)}")
            return {"error": f"Failed to stop streaming conversation: {str(e)}"}
    
    def _calculate_streaming_analytics(self, session: Dict) -> Dict[str, Any]:
        """Calculate detailed analytics for streaming conversation"""
        try:
            messages = session.get('messages', [])
            duration = (datetime.now() - session['started_at']).total_seconds() / 60  # minutes
            
            if not messages:
                return {'error': 'No conversation data available'}
            
            # Basic metrics
            total_turns = len(messages)
            total_user_words = sum(len(msg['user_message'].split()) for msg in messages)
            avg_words_per_turn = total_user_words / max(total_turns, 1)
            
            # Pronunciation analysis
            pronunciation_scores = [msg.get('pronunciation_score') for msg in messages if msg.get('pronunciation_score')]
            avg_pronunciation = sum(pronunciation_scores) / len(pronunciation_scores) if pronunciation_scores else 0
            
            # Engagement analysis
            questions_asked = sum(1 for msg in messages if '?' in msg['user_message'])
            complex_responses = sum(1 for msg in messages if len(msg['user_message'].split()) > 15)
            
            # Fluency indicators
            fluency_score = min(100, (total_user_words / max(duration, 1)) * 2)  # Words per minute * 2
            
            # Learning progress indicators
            vocabulary_complexity = self._assess_vocabulary_complexity(messages)
            conversation_flow_score = self._assess_conversation_flow(messages)
            
            return {
                'session_duration_minutes': round(duration, 1),
                'total_conversation_turns': total_turns,
                'total_words_spoken': total_user_words,
                'average_words_per_turn': round(avg_words_per_turn, 1),
                'words_per_minute': round(total_user_words / max(duration, 1), 1),
                'pronunciation_score': round(avg_pronunciation, 1),
                'fluency_score': round(fluency_score, 1),
                'questions_asked': questions_asked,
                'complex_responses': complex_responses,
                'vocabulary_complexity_score': vocabulary_complexity,
                'conversation_flow_score': conversation_flow_score,
                'engagement_level': 'high' if questions_asked > 2 else 'medium' if questions_asked > 0 else 'low',
                'recommendations': self._generate_learning_recommendations(
                    fluency_score, avg_pronunciation, vocabulary_complexity, conversation_flow_score
                ),
                'achievements': self._identify_achievements(
                    total_turns, total_user_words, avg_pronunciation, questions_asked
                ),
                'improvement_areas': self._identify_improvement_areas(
                    fluency_score, avg_pronunciation, vocabulary_complexity
                )
            }
            
        except Exception as e:
            logging.error(f"Analytics calculation error: {str(e)}")
            return {'error': 'Failed to calculate analytics'}
    
    def _assess_vocabulary_complexity(self, messages: List[Dict]) -> int:
        """Assess vocabulary complexity (0-100)"""
        try:
            complex_words = ['because', 'although', 'however', 'therefore', 'moreover', 'furthermore', 
                           'consequently', 'nevertheless', 'specifically', 'particularly', 'significantly']
            
            total_complex = 0
            total_words = 0
            
            for msg in messages:
                words = msg['user_message'].lower().split()
                total_words += len(words)
                total_complex += sum(1 for word in words if word in complex_words)
            
            if total_words == 0:
                return 0
            
            complexity_ratio = total_complex / total_words
            return min(100, int(complexity_ratio * 500))  # Scale to 0-100
            
        except:
            return 0
    
    def _assess_conversation_flow(self, messages: List[Dict]) -> int:
        """Assess conversation flow quality (0-100)"""
        try:
            if len(messages) < 2:
                return 50
            
            flow_indicators = 0
            total_checks = 0
            
            for i in range(1, len(messages)):
                prev_msg = messages[i-1]['user_message'].lower()
                curr_msg = messages[i]['user_message'].lower()
                
                total_checks += 1
                
                # Check for topic continuity
                if any(word in curr_msg for word in prev_msg.split()[-5:]):
                    flow_indicators += 1
                
                # Check for question-answer patterns
                if '?' in prev_msg and len(curr_msg.split()) > 3:
                    flow_indicators += 1
                
                # Check for elaboration
                if len(curr_msg.split()) > len(prev_msg.split()):
                    flow_indicators += 1
            
            flow_score = (flow_indicators / max(total_checks, 1)) * 100
            return min(100, int(flow_score))
            
        except:
            return 50
    
    def _generate_learning_recommendations(self, fluency: float, pronunciation: float, 
                                         vocabulary: int, flow: int) -> List[str]:
        """Generate personalized learning recommendations"""
        recommendations = []
        
        if fluency < 40:
            recommendations.append("Practice speaking daily for 10-15 minutes to build fluency")
        elif fluency < 70:
            recommendations.append("Try speaking about different topics to expand comfort zone")
        
        if pronunciation < 60:
            recommendations.append("Focus on pronunciation practice with individual sounds")
            recommendations.append("Record yourself speaking and compare with native speakers")
        
        if vocabulary < 30:
            recommendations.append("Learn 5 new advanced words each week")
            recommendations.append("Practice using connecting words like 'however' and 'therefore'")
        
        if flow < 50:
            recommendations.append("Practice asking follow-up questions in conversations")
            recommendations.append("Work on building longer, connected responses")
        
        # Always include encouragement
        recommendations.append("Keep practicing conversations - you're making great progress!")
        
        return recommendations
    
    def _identify_achievements(self, turns: int, words: int, pronunciation: float, questions: int) -> List[str]:
        """Identify student achievements"""
        achievements = []
        
        if turns >= 10:
            achievements.append("🎯 Conversation Enthusiast - Completed 10+ conversation turns!")
        
        if words >= 100:
            achievements.append("💬 Talkative Learner - Spoke 100+ words in this session!")
        
        if pronunciation >= 80:
            achievements.append("🗣️ Clear Speaker - Excellent pronunciation score!")
        
        if questions >= 3:
            achievements.append("❓ Curious Mind - Asked multiple engaging questions!")
        
        if words / max(turns, 1) >= 20:
            achievements.append("📚 Detailed Communicator - Great at explaining your thoughts!")
        
        return achievements
    
    def _identify_improvement_areas(self, fluency: float, pronunciation: float, vocabulary: int) -> List[str]:
        """Identify specific areas for improvement"""
        areas = []
        
        if fluency < 50:
            areas.append("Speaking fluency - practice daily conversations")
        
        if pronunciation < 70:
            areas.append("Pronunciation clarity - focus on difficult sounds")
        
        if vocabulary < 40:
            areas.append("Vocabulary complexity - learn advanced connecting words")
        
        return areas
    
    def get_streaming_session_status(self, session_key: str) -> Dict[str, Any]:
        """Get current status of streaming session"""
        try:
            if session_key not in self.streaming_sessions:
                return {"error": "Session not found"}
            
            session = self.streaming_sessions[session_key]
            current_time = datetime.now()
            duration = (current_time - session['started_at']).total_seconds() / 60
            
            return {
                'session_id': session['session_id'],
                'user_id': session['user_id'],
                'topic': session['topic'],
                'duration_minutes': round(duration, 1),
                'total_turns': len(session['messages']),
                'status': 'active'
            }
            
        except Exception as e:
            logging.error(f"Session status error: {str(e)}")
            return {"error": f"Failed to get session status: {str(e)}"}