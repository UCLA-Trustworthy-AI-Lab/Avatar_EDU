import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from app.api.openai_client import OpenAIClient
from app.models.session import LearningSession
from app.models.progress import Progress
from app.models.content import CustomContent
from app.models.reading import ReadingSession, ReadingMaterial, ReadingProgress, ComprehensionQuestion
from app.services.vocabulary_service import VocabularyService
from app import db

logger = logging.getLogger(__name__)

class ReadingService:
    def __init__(self):
        self.openai_client = OpenAIClient()
        self.vocabulary_service = VocabularyService()
    
    def create_reading_session(self, student_id: int, content_id: Optional[int] = None) -> LearningSession:
        session = LearningSession(
            student_id=student_id,
            module_type='reading',
            activity_type='comprehension'
        )
        
        if content_id:
            session.session_data = {'content_id': content_id}
        
        db.session.add(session)
        db.session.commit()
        return session
    
    def get_reading_content(self, difficulty_level: str = 'intermediate', topic: str = None) -> Dict:
        # Check for custom content first
        custom_content = CustomContent.query.filter_by(
            module_type='reading',
            difficulty_level=difficulty_level,
            is_active=True
        ).first()
        
        if custom_content:
            custom_content.increment_usage()
            db.session.commit()
            return custom_content.to_dict()
        
        # Generate new content using AI
        prompt = f"""
        Create a reading passage for students aged 16-20 at {difficulty_level} level.
        Topic: {topic or 'educational and engaging story'}
        
        Requirements:
        - 200-400 words
        - Age-appropriate vocabulary
        - Educational value
        - Engaging narrative
        - Include 2-3 learning objectives
        
        Format: Return title, passage, and learning objectives.
        """
        
        content = self.openai_client.generate_content(prompt)

        # Fallback if OpenAI is unavailable
        if isinstance(content, dict) and 'error' in content:
            return {
                'title': f'Reading Practice: {topic or "General"}',
                'passage': f'This is a placeholder reading passage about {topic or "an educational topic"}. Please configure your OpenAI API key in .env for AI-generated content.',
                'learning_objectives': ['Reading comprehension', 'Vocabulary building', 'Critical thinking']
            }

        return content
    
    def track_reading_performance(self, session_id: int, reading_data: Dict) -> Dict:
        session = LearningSession.query.get(session_id)
        if not session:
            return {'error': 'Session not found'}
        
        # Extract reading metrics
        reading_time = reading_data.get('reading_time_seconds', 0)
        word_count = reading_data.get('word_count', 0)
        pauses = reading_data.get('pause_count', 0)
        
        # Calculate reading speed (WPM)
        if reading_time > 0:
            words_per_minute = (word_count * 60) / reading_time
        else:
            words_per_minute = 0
        
        # Analyze reading fluency
        fluency_score = self.calculate_reading_fluency(words_per_minute, pauses, word_count)
        
        performance_data = {
            'reading_time_seconds': reading_time,
            'words_per_minute': words_per_minute,
            'pause_count': pauses,
            'fluency_score': fluency_score,
            'word_count': word_count
        }
        
        # Update session data
        current_data = session.session_data or {}
        current_data.update(performance_data)
        session.session_data = current_data
        
        db.session.commit()
        
        return performance_data
    
    def calculate_reading_fluency(self, wpm: float, pauses: int, word_count: int) -> float:
        # Age-appropriate WPM ranges for students 16-20
        if wpm >= 150:  # Advanced
            base_score = 95
        elif wpm >= 120:  # Good
            base_score = 85
        elif wpm >= 90:   # Average
            base_score = 75
        elif wpm >= 60:   # Below average
            base_score = 65
        else:             # Needs improvement
            base_score = 50
        
        # Adjust for excessive pauses
        pause_penalty = min(20, pauses * 2)
        fluency_score = max(0, base_score - pause_penalty)
        
        return fluency_score
    
    def generate_comprehension_questions(self, reading_content: str, difficulty_level: str = 'intermediate') -> List[Dict]:
        prompt = f"""
        Create 5 comprehension questions for this reading passage at {difficulty_level} level:
        
        {reading_content}
        
        Question types:
        1. Main idea (multiple choice)
        2. Detail recall (multiple choice)
        3. Inference (multiple choice)
        4. Vocabulary (multiple choice)
        5. Critical thinking (short answer)
        
        For multiple choice: provide 4 options with one correct answer.
        For short answer: provide sample acceptable answers.
        
        Return as structured JSON.
        """
        
        questions = self.openai_client.generate_content(prompt)

        # Fallback if OpenAI is unavailable
        if isinstance(questions, dict) and 'error' in questions:
            return [
                {
                    'question': 'What is the main idea of this passage?',
                    'type': 'multiple_choice',
                    'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                    'correct_answer': 'Option A',
                    'difficulty': 'medium'
                }
            ]

        return questions

    def evaluate_comprehension_answers(self, session_id: int, answers: List[str]) -> Dict:
        session = LearningSession.query.get(session_id)
        if not session:
            return {'error': 'Session not found'}
        
        questions = session.session_data.get('questions', [])
        if not questions:
            return {'error': 'No questions found for this session'}
        
        results = []
        correct_count = 0
        
        for i, (question, answer) in enumerate(zip(questions, answers)):
            if question['type'] == 'multiple_choice':
                is_correct = answer == question['correct_answer']
                if is_correct:
                    correct_count += 1
                
                results.append({
                    'question_id': i,
                    'question': question['question'],
                    'student_answer': answer,
                    'correct_answer': question['correct_answer'],
                    'is_correct': is_correct,
                    'type': 'multiple_choice'
                })
            else:  # Short answer
                score = self.evaluate_short_answer(question, answer)
                if score >= 0.7:  # 70% threshold for correct
                    correct_count += 1
                
                results.append({
                    'question_id': i,
                    'question': question['question'],
                    'student_answer': answer,
                    'score': score,
                    'feedback': self.generate_answer_feedback(question, answer, score),
                    'type': 'short_answer'
                })
        
        overall_score = (correct_count / len(questions)) * 100
        
        # Complete session
        session.complete_session(
            score=overall_score,
            data={
                'questions': questions,
                'answers': answers,
                'results': results
            }
        )
        db.session.commit()
        
        # Update progress
        self.update_reading_progress(session.student_id, session, results)
        
        return {
            'overall_score': overall_score,
            'correct_count': correct_count,
            'total_questions': len(questions),
            'detailed_results': results
        }
    
    def evaluate_short_answer(self, question: Dict, answer: str) -> float:
        # Use AI to evaluate short answers
        prompt = f"""
        Evaluate this student's answer to the reading comprehension question:
        
        Question: {question['question']}
        Sample acceptable answers: {question.get('sample_answers', [])}
        Student answer: {answer}
        
        Rate the answer from 0.0 to 1.0 based on:
        - Accuracy and completeness
        - Understanding demonstrated
        - Age-appropriate expectations (16-20 years old)
        
        Return only the numeric score.
        """
        
        try:
            score_response = self.openai_client.generate_content(prompt)
            score = float(score_response.strip())
            return max(0.0, min(1.0, score))
        except:
            return 0.5  # Default neutral score if evaluation fails
    
    def generate_answer_feedback(self, question: Dict, answer: str, score: float) -> str:
        if score >= 0.8:
            return "Excellent answer! You understood the passage well."
        elif score >= 0.6:
            return "Good answer! You're on the right track."
        else:
            return "Let's think about this together. Try reading that part again."
    
    def update_reading_progress(self, student_id: int, session: LearningSession, results: List[Dict]):
        progress = Progress.query.filter_by(
            student_id=student_id,
            module_type='reading'
        ).first()
        
        if not progress:
            progress = Progress(
                student_id=student_id,
                module_type='reading'
            )
            db.session.add(progress)
        
        progress.update_from_session(session)
        
        # Analyze comprehension strengths and weaknesses
        weak_areas = []
        strong_areas = []
        
        for result in results:
            if result.get('is_correct', False) or result.get('score', 0) >= 0.7:
                strong_areas.append("Reading comprehension")
            else:
                weak_areas.append("Reading comprehension - needs practice")
        
        # Check reading fluency
        reading_data = session.session_data or {}
        wpm = reading_data.get('words_per_minute', 0)
        if wpm < 90:  # Below average for age group
            weak_areas.append("Reading fluency - practice needed")
        elif wpm > 150:
            strong_areas.append("Excellent reading speed")
        
        progress.improvement_areas = list(set(weak_areas))
        progress.strengths = list(set(strong_areas))
        
        db.session.commit()
    
    def get_reading_recommendations(self, student_id: int) -> Dict:
        progress = Progress.query.filter_by(
            student_id=student_id,
            module_type='reading'
        ).first()
        
        if not progress:
            return {
                'recommendations': ['Start with beginner reading exercises'],
                'difficulty_level': 'beginner'
            }
        
        # Recommend based on performance
        avg_score = progress.average_score
        
        if avg_score >= 85:
            difficulty = 'advanced'
            recommendations = [
                'Try more challenging texts',
                'Focus on critical thinking questions',
                'Explore different genres'
            ]
        elif avg_score >= 70:
            difficulty = 'intermediate'
            recommendations = [
                'Continue with current level',
                'Practice inference questions',
                'Work on reading speed'
            ]
        else:
            difficulty = 'beginner'
            recommendations = [
                'Focus on basic comprehension',
                'Practice with shorter texts',
                'Work on vocabulary building'
            ]
        
        return {
            'recommendations': recommendations,
            'difficulty_level': difficulty,
            'focus_areas': progress.improvement_areas or []
        }
    
    def create_interactive_reading_session(self, student_id: int, material_id: int) -> Dict:
        """
        Create an interactive reading session with vocabulary support
        
        Args:
            student_id: ID of the student
            material_id: ID of the reading material
            
        Returns:
            Dictionary containing session data and reading material
        """
        try:
            # Get reading material
            material = ReadingMaterial.query.get(material_id)
            if not material or not material.is_active:
                return {'error': 'Reading material not found or inactive'}
            
            # Create learning session
            learning_session = LearningSession(
                student_id=student_id,
                module_type='reading',
                activity_type='interactive_reading'
            )
            db.session.add(learning_session)
            db.session.flush()  # Get the ID
            
            # Create reading session
            reading_session = ReadingSession(
                student_id=student_id,
                session_id=learning_session.id,
                text_title=material.title,
                text_content=material.content,
                text_difficulty_level=material.difficulty_level,
                text_category=material.category,
                total_words_read=material.word_count
            )
            db.session.add(reading_session)
            db.session.commit()
            
            # Prepare response with interactive text
            interactive_text = self._prepare_interactive_text(material.content)
            
            return {
                'session_id': reading_session.id,
                'learning_session_id': learning_session.id,
                'material': {
                    'id': material.id,
                    'title': material.title,
                    'difficulty_level': material.difficulty_level,
                    'category': material.category,
                    'word_count': material.word_count,
                    'estimated_reading_time': material.estimated_reading_time
                },
                'interactive_text': interactive_text,
                'instructions': {
                    'click_words': 'Click on any word to see its definition, pronunciation, and examples',
                    'chinese_translation': 'Double-click for Chinese translation',
                    'progress_tracking': 'Your reading speed and vocabulary learning are being tracked'
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating interactive reading session: {e}")
            return {'error': 'Failed to create reading session'}
    
    def handle_word_click(self, student_id: int, reading_session_id: int, word: str, 
                         include_chinese: bool = False) -> Dict:
        """
        Handle word click during interactive reading
        
        Args:
            student_id: ID of the student
            reading_session_id: ID of the reading session
            word: The word that was clicked
            include_chinese: Whether to include Chinese translation
            
        Returns:
            Dictionary containing word information
        """
        try:
            if include_chinese:
                return self.vocabulary_service.get_word_with_chinese_translation(
                    student_id, reading_session_id, word
                )
            else:
                return self.vocabulary_service.process_word_click(
                    student_id, reading_session_id, word
                )
                
        except Exception as e:
            logger.error(f"Error handling word click: {e}")
            # Return basic fallback word data instead of error
            return {
                'word': word,
                'definition': 'Definition not available. Please configure API keys in .env.',
                'pronunciation': '',
                'examples': [],
                'synonyms': [],
                'chinese_translation': f'[{word}的中文翻译]' if include_chinese else None,
                'difficulty_level': 5,
                'looked_up_count': 1,
                'is_mastered': False,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def update_reading_progress_realtime(self, reading_session_id: int, progress_data: Dict) -> Dict:
        """
        Update reading progress in real-time during reading session
        
        Args:
            reading_session_id: ID of the reading session
            progress_data: Dictionary containing progress metrics
            
        Returns:
            Updated progress information
        """
        try:
            session = ReadingSession.query.get(reading_session_id)
            if not session:
                return {'error': 'Reading session not found'}
            
            # Update reading session metrics
            if 'words_read' in progress_data:
                session.total_words_read = progress_data['words_read']
            
            if 'time_spent' in progress_data:
                session.time_spent_reading = progress_data['time_spent']
                
                # Calculate WPM
                if progress_data['time_spent'] > 0:
                    session.words_per_minute = (session.total_words_read * 60) / progress_data['time_spent']
            
            if 'completion_percentage' in progress_data:
                session.reading_completion_percentage = progress_data['completion_percentage']
            
            if 'vocabulary_clicks' in progress_data:
                session.vocabulary_clicks = progress_data['vocabulary_clicks']
            
            db.session.commit()
            
            return {
                'session_id': reading_session_id,
                'words_per_minute': session.words_per_minute,
                'completion_percentage': session.reading_completion_percentage,
                'vocabulary_interactions': session.vocabulary_clicks,
                'reading_time': session.time_spent_reading
            }
            
        except Exception as e:
            logger.error(f"Error updating reading progress: {e}")
            return {'error': 'Failed to update progress'}
    
    def complete_reading_session(self, reading_session_id: int, final_data: Dict) -> Dict:
        """
        Complete a reading session and calculate final scores.
        NOW WITH MEMORY TRACKING: Extracts insights and updates student memory board.

        Args:
            reading_session_id: ID of the reading session
            final_data: Final reading metrics

        Returns:
            Session completion summary with recommendations
        """
        try:
            session = ReadingSession.query.get(reading_session_id)
            if not session:
                return {'error': 'Reading session not found'}

            # Update final metrics
            session.completed_at = datetime.utcnow()
            session.time_spent_reading = final_data.get('total_time', session.time_spent_reading)
            session.reading_completion_percentage = final_data.get('completion_percentage', 100)
            session.vocabulary_clicks = final_data.get('vocabulary_clicks', session.vocabulary_clicks)
            session.new_words_learned = final_data.get('new_words_learned', 0)

            # Calculate final WPM
            if session.time_spent_reading > 0:
                session.words_per_minute = (session.total_words_read * 60) / session.time_spent_reading

            # Generate comprehension questions
            comprehension_questions = self._generate_adaptive_questions(session)

            db.session.commit()

            # Update long-term progress
            self._update_long_term_reading_progress(session)

            # Get vocabulary statistics
            vocab_stats = self.vocabulary_service.get_student_vocabulary_stats(session.student_id)

            # === MEMORY BOARD INTEGRATION ===
            # Extract insights from this session (mistakes, patterns, challenges)
            from app.services.memory_service import get_memory_service
            memory_service = get_memory_service()

            try:
                # Extract insights
                insight = memory_service.extract_reading_session_insights(
                    student_id=session.student_id,
                    reading_session_id=reading_session_id
                )
                logger.info(f"Extracted memory insights for reading session {reading_session_id}")

                # Check if we should compress memory
                if memory_service.should_compress_reading_memory(session.student_id):
                    logger.info(f"Compressing reading memory for student {session.student_id}")
                    compressed = memory_service.compress_reading_memory(
                        student_id=session.student_id,
                        use_ai=True
                    )
                    logger.info(f"Memory compression complete. Summary: {compressed.get('summary', 'N/A')[:100]}")

            except Exception as mem_error:
                logger.error(f"Memory tracking error (non-fatal): {mem_error}")
                # Don't fail the whole session if memory tracking fails

            # === END MEMORY BOARD INTEGRATION ===

            return {
                'session_summary': {
                    'session_id': reading_session_id,
                    'text_title': session.text_title,
                    'reading_time_minutes': round(session.time_spent_reading / 60, 1),
                    'words_per_minute': round(session.words_per_minute, 1),
                    'completion_percentage': session.reading_completion_percentage,
                    'vocabulary_interactions': session.vocabulary_clicks,
                    'new_words_learned': session.new_words_learned
                },
                'comprehension_questions': comprehension_questions,
                'vocabulary_stats': vocab_stats,
                'recommendations': self._generate_reading_recommendations(session)
            }

        except Exception as e:
            logger.error(f"Error completing reading session: {e}")
            return {'error': 'Failed to complete session'}
    
    def get_reading_materials_for_student(self, student_id: int, category: str = None, 
                                        difficulty: str = None) -> List[Dict]:
        """
        Get available reading materials for a student based on their level and preferences
        
        Args:
            student_id: ID of the student
            category: Optional category filter
            difficulty: Optional difficulty filter
            
        Returns:
            List of available reading materials
        """
        try:
            # Get student info for personalization
            from app.models.user import Student
            student = Student.query.get(student_id)
            
            query = ReadingMaterial.query.filter_by(is_active=True)
            
            # Apply filters
            if category:
                query = query.filter_by(category=category)
            
            if difficulty:
                query = query.filter_by(difficulty_level=difficulty)
            elif student:
                # Auto-suggest difficulty based on student level
                if student.english_proficiency_level == 'beginner':
                    query = query.filter(ReadingMaterial.difficulty_level.in_(['beginner', 'intermediate']))
                elif student.english_proficiency_level == 'advanced':
                    query = query.filter(ReadingMaterial.difficulty_level.in_(['intermediate', 'advanced', 'expert']))
            
            materials = query.order_by(ReadingMaterial.created_at.desc()).limit(20).all()
            
            return [{
                'id': material.id,
                'title': material.title,
                'difficulty_level': material.difficulty_level,
                'category': material.category,
                'word_count': material.word_count,
                'estimated_reading_time': material.estimated_reading_time,
                'tags': material.tags or [],
                'target_exams': material.target_exams or []
            } for material in materials]
            
        except Exception as e:
            logger.error(f"Error getting reading materials: {e}")
            return []
    
    def get_material_by_id(self, material_id: int) -> Dict:
        """
        Get a specific reading material by ID including full content
        
        Args:
            material_id: ID of the material
            
        Returns:
            Dictionary with material data including content
        """
        try:
            material = ReadingMaterial.query.filter_by(id=material_id, is_active=True).first()
            
            if not material:
                return None
                
            return {
                'id': material.id,
                'title': material.title,
                'content': material.content,
                'difficulty_level': material.difficulty_level,
                'category': material.category,
                'word_count': material.word_count,
                'estimated_reading_time': material.estimated_reading_time,
                'tags': material.tags,
                'target_exams': material.target_exams,
                'created_at': material.created_at.isoformat() if material.created_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting material by ID {material_id}: {e}")
            return None
    
    def _prepare_interactive_text(self, text: str) -> Dict:
        """
        Prepare text for interactive reading by adding word boundaries and metadata
        
        Args:
            text: Raw text content
            
        Returns:
            Dictionary with interactive text data
        """
        import re
        
        # Split text into sentences and words
        sentences = re.split(r'[.!?]+', text)
        interactive_sentences = []
        
        for sentence in sentences:
            if sentence.strip():
                words = re.findall(r'\b[\w\']+\b|\W+', sentence)
                interactive_words = []
                
                for word in words:
                    if re.match(r'\b[\w\']+\b', word):  # Is a word
                        interactive_words.append({
                            'text': word,
                            'type': 'word',
                            'clickable': True
                        })
                    else:  # Is punctuation/whitespace
                        interactive_words.append({
                            'text': word,
                            'type': 'punctuation',
                            'clickable': False
                        })
                
                interactive_sentences.append({
                    'words': interactive_words,
                    'sentence_text': sentence.strip()
                })
        
        return {
            'sentences': interactive_sentences,
            'total_words': len(re.findall(r'\b[\w\']+\b', text)),
            'total_sentences': len([s for s in sentences if s.strip()])
        }
    
    def _generate_adaptive_questions(self, session: ReadingSession) -> List[Dict]:
        """Generate comprehension questions adapted to the student's performance"""
        try:
            # Customize questions based on student's vocabulary interactions
            vocab_focus = session.vocabulary_clicks > session.total_words_read * 0.1  # High vocab interaction
            
            prompt = f"""
            Create 5 comprehension questions for high school/college students (ages 16-20) based on this text:
            
            Title: {session.text_title}
            Text: {session.text_content[:1000]}...
            
            Student context:
            - Difficulty level: {session.text_difficulty_level}
            - Category: {session.text_category}
            - Vocabulary interactions: {session.vocabulary_clicks} words clicked
            - Focus on vocabulary: {vocab_focus}
            
            Question types needed:
            1. Main idea and theme analysis
            2. Critical thinking and inference
            3. Vocabulary in context {'(prioritize since student clicked many words)' if vocab_focus else ''}
            4. Text structure and organization
            5. Application to real-world scenarios
            
            Format: JSON array with question, type, options (for multiple choice), correct_answer, explanation
            Make questions appropriate for Chinese students learning English.
            """
            
            questions_data = self.openai_client.generate_content(prompt)

            # Fallback if OpenAI is unavailable
            if isinstance(questions_data, dict) and 'error' in questions_data:
                return []

            if isinstance(questions_data, str):
                questions_data = json.loads(questions_data)

            return questions_data.get('questions', []) if isinstance(questions_data, dict) else questions_data
            
        except Exception as e:
            logger.error(f"Error generating adaptive questions: {e}")
            return []
    
    def _update_long_term_reading_progress(self, session: ReadingSession):
        """Update student's long-term reading progress"""
        try:
            progress = ReadingProgress.query.filter_by(student_id=session.student_id).first()
            
            if not progress:
                progress = ReadingProgress(student_id=session.student_id)
                db.session.add(progress)
            
            # Update cumulative metrics
            progress.total_words_read += session.total_words_read
            
            # Update average reading speed (weighted average)
            if progress.average_reading_speed == 0:
                progress.average_reading_speed = session.words_per_minute
            else:
                progress.average_reading_speed = (progress.average_reading_speed * 0.8 + 
                                                session.words_per_minute * 0.2)
            
            # Update vocabulary size estimate
            vocab_interactions = self.vocabulary_service.get_student_vocabulary_stats(session.student_id)
            progress.vocabulary_size = vocab_interactions.get('words_mastered', 0)
            
            progress.last_reading_session = datetime.utcnow()
            progress.updated_at = datetime.utcnow()
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating long-term reading progress: {e}")
    
    def _generate_reading_recommendations(self, session: ReadingSession) -> List[str]:
        """Generate personalized reading recommendations"""
        recommendations = []
        
        # Reading speed recommendations
        wpm = session.words_per_minute
        if wpm < 200:  # Below average for college students
            recommendations.append("Practice reading speed with timed exercises")
            recommendations.append("Try reading simpler texts to build fluency first")
        elif wpm > 350:  # Very fast
            recommendations.append("Excellent reading speed! Focus on comprehension depth")
        
        # Vocabulary recommendations
        vocab_ratio = session.vocabulary_clicks / session.total_words_read if session.total_words_read > 0 else 0
        if vocab_ratio > 0.15:  # High vocabulary lookup rate
            recommendations.append("Focus on vocabulary building before tackling harder texts")
            recommendations.append("Review the words you looked up to reinforce learning")
        elif vocab_ratio < 0.05:  # Very low lookup rate
            recommendations.append("Challenge yourself with more advanced vocabulary")
        
        # Content recommendations
        if session.text_category == 'academic':
            recommendations.append("Continue with academic texts to prepare for exams")
        elif session.text_category == 'news':
            recommendations.append("Try academic papers to challenge your skills")
        
        return recommendations[:3]  # Limit to top 3 recommendations