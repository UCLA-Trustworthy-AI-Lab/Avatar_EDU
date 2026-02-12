import logging
from typing import Dict, List, Optional
from datetime import datetime
from app.api.openai_client import OpenAIClient
from app.models.reading import ReadingSession, VocabularyInteraction
from app.models.user import Student
from app import db

logger = logging.getLogger(__name__)

class ReadingChatbotService:
    """AI chatbot service specifically for reading comprehension assistance"""
    
    def __init__(self):
        self.openai_client = OpenAIClient()
        self.conversation_history = {}  # Store conversation history per session
    
    def get_contextual_response(self, student_id: int, reading_session_id: int,
                               user_message: str, message_type: str = "general") -> Dict:
        """
        Generate contextual AI response based on current reading session.
        NOW WITH MEMORY: Uses student's learning history to personalize responses.

        Args:
            student_id: ID of the student
            reading_session_id: Current reading session ID
            user_message: User's question or message
            message_type: Type of help needed (word_explanation, comprehension, general)

        Returns:
            Dictionary containing AI response and relevant context
        """
        try:
            # Get reading session context
            session = ReadingSession.query.get(reading_session_id)
            if not session:
                return {
                    'response': "I'm sorry, I couldn't find your current reading session. Please start a reading session first.",
                    'type': 'error'
                }

            # Get student info for personalization
            student = Student.query.get(student_id)

            # === NEW: Load memory board ===
            from app.services.memory_service import get_memory_service
            memory_service = get_memory_service()
            student_memory = memory_service.get_reading_memory(student_id)
            adaptive_hints = memory_service.get_adaptive_question_focus(student_id)

            memory_context_used = bool(student_memory)  # Track if memory was available
            # === END MEMORY LOAD ===

            # Build context for AI (now includes memory)
            context = self._build_reading_context(session, student, reading_session_id)
            context['memory'] = student_memory  # Add memory to context
            context['adaptive_hints'] = adaptive_hints
            
            # Generate appropriate prompt based on message type
            if message_type == "word_explanation":
                prompt = self._create_word_explanation_prompt(context, user_message)
            elif message_type == "comprehension":
                prompt = self._create_comprehension_prompt(context, user_message)
            elif message_type == "reading_help":
                prompt = self._create_reading_help_prompt(context, user_message)
            else:
                prompt = self._create_general_prompt(context, user_message)
            
            # Get AI response
            ai_response = self.openai_client.generate_content(prompt)

            # Extract content from response
            response_text = ai_response.get('content', ai_response) if isinstance(ai_response, dict) else str(ai_response)

            # Store conversation history (old method)
            self._store_conversation(reading_session_id, user_message, response_text)

            # === NEW: Save to database for memory board ===
            self._save_chatbot_interaction(
                student_id=student_id,
                reading_session_id=reading_session_id,
                user_message=user_message,
                chatbot_response=response_text,
                message_type=message_type,
                memory_context_used=memory_context_used
            )
            # === END DATABASE SAVE ===

            return {
                'response': response_text,
                'type': 'success',
                'memory_aware': memory_context_used,  # NEW: Tell frontend if memory was used
                'context_used': {
                    'text_title': session.text_title,
                    'difficulty_level': session.text_difficulty_level,
                    'student_level': student.english_proficiency_level if student else 'intermediate'
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating contextual response: {e}")
            return {
                'response': "I'm sorry, I encountered an error. Please try asking your question again.",
                'type': 'error'
            }
    
    def explain_word_in_context(self, student_id: int, reading_session_id: int, 
                               word: str, sentence_context: str = "") -> Dict:
        """
        Explain a specific word within the context of the reading material
        
        Args:
            student_id: ID of the student
            reading_session_id: Current reading session ID
            word: Word to explain
            sentence_context: The sentence containing the word
            
        Returns:
            Dictionary containing detailed word explanation
        """
        try:
            session = ReadingSession.query.get(reading_session_id)
            student = Student.query.get(student_id)
            
            # Check if student has interacted with this word before
            previous_interaction = VocabularyInteraction.query.filter_by(
                student_id=student_id,
                word=word.lower()
            ).first()
            
            context = {
                'word': word,
                'sentence_context': sentence_context,
                'text_title': session.text_title if session else "Unknown",
                'text_category': session.text_category if session else "general",
                'student_level': student.english_proficiency_level if student else 'intermediate',
                'previous_lookups': previous_interaction.looked_up_count if previous_interaction else 0,
                'is_mastered': previous_interaction.is_mastered if previous_interaction else False
            }
            
            prompt = f"""
            You are an AI English tutor helping a Chinese student (proficiency level: {context['student_level']}) 
            understand vocabulary in context while reading "{context['text_title']}" ({context['text_category']} text).
            
            The student is asking about the word: "{word}"
            Context sentence: "{sentence_context}"
            
            Student interaction history with this word:
            - Previous lookups: {context['previous_lookups']}
            - Already mastered: {context['is_mastered']}
            
            Please provide a helpful explanation that includes:
            1. The meaning of "{word}" in this specific context
            2. Why this meaning fits the sentence
            3. Any nuances or connotations relevant to the text
            4. A simpler synonym if the word is difficult
            5. How this word commonly appears in {context['text_category']} texts
            
            Keep your explanation clear, encouraging, and appropriate for a {context['student_level']} level student.
            If they've looked up this word before, acknowledge that and help reinforce the learning.
            """
            
            ai_response = self.openai_client.generate_content(prompt)
            response_text = ai_response.get('content', ai_response) if isinstance(ai_response, dict) else str(ai_response)
            
            return {
                'response': response_text,
                'type': 'word_explanation',
                'word': word,
                'context': context
            }
            
        except Exception as e:
            logger.error(f"Error explaining word in context: {e}")
            return {
                'response': f"I can help explain '{word}', but I'm having trouble accessing the context right now. Could you try again?",
                'type': 'error'
            }
    
    def get_reading_comprehension_help(self, student_id: int, reading_session_id: int, 
                                     question: str) -> Dict:
        """
        Provide reading comprehension assistance
        
        Args:
            student_id: ID of the student
            reading_session_id: Current reading session ID
            question: Student's comprehension question
            
        Returns:
            Dictionary containing comprehension guidance
        """
        try:
            session = ReadingSession.query.get(reading_session_id)
            student = Student.query.get(student_id)
            
            if not session:
                return {
                    'response': "Please start a reading session first so I can help with comprehension questions.",
                    'type': 'error'
                }
            
            # Get text excerpt for context (first 500 chars)
            text_excerpt = session.text_content[:500] + "..." if len(session.text_content) > 500 else session.text_content
            
            prompt = f"""
            You are an AI English tutor helping a Chinese student (level: {student.english_proficiency_level if student else 'intermediate'}) 
            with reading comprehension.
            
            Current reading material: "{session.text_title}"
            Category: {session.text_category}
            Difficulty: {session.text_difficulty_level}
            
            Text excerpt: "{text_excerpt}"
            
            Student's question: "{question}"
            
            Please provide helpful guidance that:
            1. Addresses their specific question
            2. Guides them to find the answer rather than giving it directly
            3. Explains relevant reading strategies
            4. Connects to exam preparation if relevant ({session.text_category})
            5. Encourages critical thinking
            
            Be supportive and educational, helping them become a better reader.
            """
            
            ai_response = self.openai_client.generate_content(prompt)
            response_text = ai_response.get('content', ai_response) if isinstance(ai_response, dict) else str(ai_response)
            
            return {
                'response': response_text,
                'type': 'comprehension_help',
                'reading_context': {
                    'title': session.text_title,
                    'category': session.text_category,
                    'difficulty': session.text_difficulty_level
                }
            }
            
        except Exception as e:
            logger.error(f"Error providing comprehension help: {e}")
            return {
                'response': "I'd be happy to help with comprehension questions. Could you try asking again?",
                'type': 'error'
            }
    
    def get_reading_strategy_tips(self, student_id: int, reading_session_id: int) -> Dict:
        """
        Provide personalized reading strategy tips based on current performance
        
        Args:
            student_id: ID of the student
            reading_session_id: Current reading session ID
            
        Returns:
            Dictionary containing reading strategy recommendations
        """
        try:
            session = ReadingSession.query.get(reading_session_id)
            student = Student.query.get(student_id)
            
            # Analyze current reading performance
            total_words = session.total_words_read or 0
            vocab_clicks = session.vocabulary_clicks or 0
            vocab_click_rate = (vocab_clicks / total_words if total_words > 0 else 0)
            
            reading_speed = session.words_per_minute or 0
            
            prompt = f"""
            You are an AI English tutor providing personalized reading strategy tips for a Chinese student.
            
            Student profile:
            - English level: {student.english_proficiency_level if student else 'intermediate'}
            - Target exams: {student.target_exams if student and student.target_exams else ['general improvement']}
            
            Current reading session:
            - Text: "{session.text_title}"
            - Category: {session.text_category}
            - Difficulty: {session.text_difficulty_level}
            - Current reading speed: {reading_speed} WPM
            - Vocabulary lookup rate: {vocab_click_rate:.1%}
            
            Based on this data, provide 3-4 specific, actionable reading strategy tips that will help them:
            1. Improve their reading speed if it's below target
            2. Better handle vocabulary if they're looking up too many words
            3. Enhance comprehension for this type of text
            4. Prepare for their target exams
            
            Make the tips encouraging and practical for their current level.
            """
            
            ai_response = self.openai_client.generate_content(prompt)
            response_text = ai_response.get('content', ai_response) if isinstance(ai_response, dict) else str(ai_response)
            
            return {
                'response': response_text,
                'type': 'strategy_tips',
                'performance_data': {
                    'reading_speed': reading_speed,
                    'vocab_click_rate': f"{vocab_click_rate:.1%}",
                    'text_difficulty': session.text_difficulty_level
                }
            }
            
        except Exception as e:
            logger.error(f"Error providing strategy tips: {e}")
            return {
                'response': "I can provide reading strategy tips to help improve your performance. What specific area would you like help with?",
                'type': 'error'
            }
    
    def _build_reading_context(self, session: ReadingSession, student: Student, 
                              reading_session_id: int) -> Dict:
        """Build comprehensive context for AI responses"""
        
        # Get recent vocabulary interactions
        recent_words = VocabularyInteraction.query.filter_by(
            student_id=student.id,
            reading_session_id=reading_session_id
        ).order_by(VocabularyInteraction.interaction_timestamp.desc()).limit(5).all()
        
        # Get conversation history for this session
        conversation_history = self.conversation_history.get(reading_session_id, [])
        
        return {
            'text_title': session.text_title,
            'text_category': session.text_category,
            'text_difficulty': session.text_difficulty_level,
            'text_excerpt': session.text_content[:300] + "..." if session.text_content else "",
            'student_level': student.english_proficiency_level if student else 'intermediate',
            'student_age': student.age if student else 18,
            'target_exams': student.target_exams if student and student.target_exams else [],
            'reading_speed': session.words_per_minute or 0,
            'vocabulary_clicks': session.vocabulary_clicks or 0,
            'recent_words': [w.word for w in recent_words],
            'conversation_history': conversation_history[-3:]  # Last 3 exchanges
        }
    
    def _create_word_explanation_prompt(self, context: Dict, user_message: str) -> str:
        """Create prompt for word explanation requests"""
        return f"""
        You are an AI English tutor helping a Chinese student (level: {context['student_level']}) 
        understand vocabulary while reading "{context['text_title']}" ({context['text_category']}).
        
        Recent vocabulary they've looked up: {', '.join(context['recent_words'])}
        Their question: "{user_message}"
        
        Provide a clear, helpful explanation focusing on:
        1. The specific meaning in this reading context
        2. Usage examples relevant to {context['text_category']} texts
        3. Tips for remembering this word
        4. How it relates to their {context['target_exams']} preparation if applicable
        
        Be encouraging and educational.
        """
    
    def _create_comprehension_prompt(self, context: Dict, user_message: str) -> str:
        """Create prompt for comprehension questions"""
        return f"""
        You are an AI English tutor helping with reading comprehension for "{context['text_title']}" 
        ({context['text_category']} text, {context['text_difficulty']} level).
        
        Text context: {context['text_excerpt']}
        Student level: {context['student_level']}
        Student's question: "{user_message}"
        
        Provide guidance that:
        1. Helps them understand the text better
        2. Teaches reading strategies
        3. Connects to exam preparation skills
        4. Encourages critical thinking
        
        Guide them to the answer rather than giving it directly.
        """
    
    def _create_reading_help_prompt(self, context: Dict, user_message: str) -> str:
        """Create prompt for general reading help"""
        return f"""
        You are an AI English tutor providing reading assistance to a Chinese student.
        
        Current reading: "{context['text_title']}" ({context['text_category']}, {context['text_difficulty']} level)
        Student level: {context['student_level']}
        Reading speed: {context['reading_speed']} WPM
        Student's request: "{user_message}"
        
        Provide helpful, personalized advice for improving their reading skills.
        Focus on practical strategies they can use immediately.
        """
    
    def _create_general_prompt(self, context: Dict, user_message: str) -> str:
        """Create prompt for general questions (NOW WITH MEMORY AWARENESS)"""

        # Build memory context string
        memory_context = ""
        if context.get('memory') and context['memory'].get('summary'):
            memory_summary = context['memory'].get('summary', '')
            vocab_gaps = context['memory'].get('vocabulary_gaps', [])
            comp_weak = context['memory'].get('comprehension_weaknesses', [])

            memory_context = f"""
        🧠 MEMORY BOARD - What I remember about this student:
        {memory_summary[:200]}

        Known challenges:"""

            if vocab_gaps:
                vocab_words = [v.get('word', '') for v in vocab_gaps[:3]]
                memory_context += f"\n        - Vocabulary struggles: {', '.join(vocab_words)}"

            if comp_weak:
                weak_skills = [w.get('skill', '') for w in comp_weak[:2]]
                memory_context += f"\n        - Comprehension weaknesses: {', '.join(weak_skills)}"

            memory_context += "\n\n        ⚡ Use this memory to personalize your response! Reference their past struggles when relevant."

        return f"""
        You are a friendly and knowledgeable English teacher helping a Chinese student (level: {context['student_level']})
        who is reading "{context['text_title']}" ({context['text_category']}).
        {memory_context}

        YOUR ROLE:
        - Help with ALL aspects of English learning: vocabulary, grammar, pronunciation, writing, speaking, culture, idioms, expressions
        - Answer questions about English-speaking countries, culture, and customs (as they relate to language learning)
        - Explain differences between American and British English
        - Help with exam preparation for {context.get('target_exams', ['English proficiency tests'])}
        - Provide conversation practice and examples
        - Explain slang, informal language, and how English is actually used
        - Discuss English literature, movies, songs, and media (for learning purposes)
        - Help with pronunciation, intonation, and speaking confidence

        BE SUPPORTIVE AND ENCOURAGING:
        - Answer questions patiently and thoroughly
        - Provide practical examples and real-world usage
        - Connect topics to their daily English learning
        - Share learning tips and strategies
        - Make learning enjoyable and engaging
        - IF the memory board shows they've struggled with this topic before, acknowledge it warmly:
          "I remember you were working on [topic] before. Let's tackle this together!"

        Student's message: "{user_message}"
        Current reading: {context['text_excerpt']}

        Respond as a helpful English teacher who REMEMBERS this student's learning journey!
        """
    
    def _store_conversation(self, reading_session_id: int, user_message: str, ai_response: str):
        """Store conversation history for context"""
        if reading_session_id not in self.conversation_history:
            self.conversation_history[reading_session_id] = []

        self.conversation_history[reading_session_id].append({
            'user': user_message,
            'assistant': ai_response,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Keep only last 10 exchanges to manage memory
        if len(self.conversation_history[reading_session_id]) > 10:
            self.conversation_history[reading_session_id] = self.conversation_history[reading_session_id][-10:]

    def _save_chatbot_interaction(self, student_id: int, reading_session_id: int,
                                  user_message: str, chatbot_response: str,
                                  message_type: str, memory_context_used: bool):
        """
        Save chatbot interaction to database for memory board tracking.

        This is how we learn what confuses students!
        """
        try:
            from app.models.reading import ChatbotInteraction

            # Extract topic from the message
            topic_category = self._extract_topic_from_message(user_message, message_type)

            # Check if this is a repeated topic
            previous_same_topic = ChatbotInteraction.query.filter_by(
                student_id=student_id,
                topic_category=topic_category
            ).filter(
                ChatbotInteraction.reading_session_id != reading_session_id
            ).count()

            is_repeated_topic = previous_same_topic > 0

            # Estimate confusion level based on message phrasing
            confusion_level = self._estimate_confusion_level(user_message)

            # Create interaction record
            interaction = ChatbotInteraction(
                student_id=student_id,
                reading_session_id=reading_session_id,
                user_message=user_message,
                chatbot_response=chatbot_response,
                message_type=message_type,
                topic_category=topic_category,
                confusion_level=confusion_level,
                is_repeated_topic=is_repeated_topic,
                memory_context_used=memory_context_used
            )

            db.session.add(interaction)
            db.session.commit()

            logger.info(f"Saved chatbot interaction: topic={topic_category}, repeated={is_repeated_topic}")

        except Exception as e:
            logger.error(f"Error saving chatbot interaction: {e}")
            # Don't fail the chatbot response if saving fails
            db.session.rollback()

    def _extract_topic_from_message(self, message: str, message_type: str) -> str:
        """
        Extract topic category from user message.

        Returns categories like: grammar, vocabulary, comprehension, inference, main_idea, etc.
        """
        message_lower = message.lower()

        # Keyword mapping
        if message_type == "word_explanation":
            return "vocabulary"
        elif message_type == "comprehension":
            return "comprehension"

        # Grammar indicators
        if any(word in message_lower for word in ['grammar', 'tense', 'verb', 'noun', 'adjective', 'pronoun', 'preposition', 'passive', 'active']):
            return "grammar"

        # Vocabulary indicators
        if any(word in message_lower for word in ['word', 'meaning', 'definition', 'synonym', 'vocabulary', 'phrase', 'expression']):
            return "vocabulary"

        # Comprehension indicators
        if any(word in message_lower for word in ['understand', 'mean', 'main idea', 'inference', 'imply', 'suggest', 'conclude']):
            return "comprehension"

        # Inference specific
        if any(word in message_lower for word in ['infer', 'imply', 'suggest', 'hint', 'indirectly']):
            return "inference"

        # Reading strategy
        if any(word in message_lower for word in ['how to read', 'strategy', 'improve reading', 'read faster', 'comprehension skill']):
            return "reading_strategy"

        # Default
        return "general"

    def _estimate_confusion_level(self, message: str) -> str:
        """
        Estimate how confused the student is based on message phrasing.

        Returns: 'low', 'medium', 'high'
        """
        message_lower = message.lower()

        # High confusion indicators
        high_confusion_phrases = [
            "don't understand", "confused", "no idea", "can't figure out",
            "completely lost", "what does this mean", "help me", "i'm stuck"
        ]

        # Low confusion indicators (more specific questions)
        low_confusion_phrases = [
            "can you explain", "what is the difference", "how do you use",
            "is this correct", "could you clarify"
        ]

        if any(phrase in message_lower for phrase in high_confusion_phrases):
            return "high"
        elif any(phrase in message_lower for phrase in low_confusion_phrases):
            return "medium"
        else:
            return "low"