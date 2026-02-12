import json
import base64
from typing import Dict, List, Optional
from app.api.openai_client import OpenAIClient
from app.api.ocr_client import OCRClient
from app.models.session import LearningSession
from app.models.progress import Progress
from app.models.content import CustomContent
from app.models.user import Student
from app import db

class WritingService:
    def __init__(self):
        self.openai_client = OpenAIClient()
        self.ocr_client = OCRClient()
    
    def create_writing_session(self, student_id: int, activity_type: str = 'creative_writing') -> LearningSession:
        session = LearningSession(
            student_id=student_id,
            module_type='writing',
            activity_type=activity_type
        )
        db.session.add(session)
        db.session.commit()
        return session
    
    def generate_writing_prompt(self, student_id: int, topic_type: str = 'creative') -> Dict:
        # Get student info for personalized prompts
        student = Student.query.get(student_id)
        if not student:
            return {'error': 'Student not found'}
        
        # Check student's writing progress for adaptive difficulty
        progress = Progress.query.filter_by(
            student_id=student_id,
            module_type='writing'
        ).first()
        
        difficulty_level = 'intermediate'
        if progress:
            if progress.average_score >= 85:
                difficulty_level = 'advanced'
            elif progress.average_score < 60:
                difficulty_level = 'beginner'
        
        # Check for custom teacher prompts
        custom_prompt = CustomContent.query.filter_by(
            module_type='writing',
            content_type='prompt',
            difficulty_level=difficulty_level,
            is_active=True
        ).first()
        
        if custom_prompt:
            custom_prompt.increment_usage()
            db.session.commit()
            return custom_prompt.to_dict()
        
        # Generate AI prompt based on student performance and preferences
        prompt_request = f"""
        Create a {topic_type} writing prompt for a {student.age}-year-old student at {difficulty_level} level.
        
        Requirements:
        - Age-appropriate and engaging
        - Clear instructions
        - 150-300 word target length
        - Include 2-3 specific elements to include
        - Provide writing tips
        
        Topic type: {topic_type}
        Return: title, prompt, word_target, writing_tips, evaluation_criteria
        """
        
        prompt_data = self.openai_client.generate_content(prompt_request)
        return prompt_data
    
    def process_handwritten_submission(self, image_file_path: str) -> Dict:
        # Extract text from handwritten image using OCR
        try:
            extracted_text = self.ocr_client.extract_text_from_image(image_file_path)
            
            # Clean and validate extracted text
            cleaned_text = self.clean_extracted_text(extracted_text)
            
            confidence_score = self.ocr_client.get_confidence_score()
            
            return {
                'success': True,
                'extracted_text': cleaned_text,
                'confidence_score': confidence_score,
                'word_count': len(cleaned_text.split()),
                'needs_review': confidence_score < 0.8
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Could not process handwritten text. Please try typing your response.'
            }
    
    def clean_extracted_text(self, raw_text: str) -> str:
        # Clean up OCR artifacts and common errors
        cleaned = raw_text.strip()
        
        # Remove common OCR errors
        replacements = {
            '|': 'I',
            '0': 'o',  # Context-dependent
            '5': 's',  # Context-dependent
            '1': 'l',  # Context-dependent
        }
        
        # Apply basic cleaning (more sophisticated logic could be added)
        for old, new in replacements.items():
            # Only replace in specific contexts to avoid over-correction
            pass
        
        return cleaned
    
    def evaluate_writing_submission(self, session_id: int, text: str, prompt_data: Dict) -> Dict:
        session = LearningSession.query.get(session_id)
        if not session:
            return {'error': 'Session not found'}
        
        # Comprehensive writing evaluation using AI
        evaluation_prompt = f"""
        Evaluate this student's writing (age 8-14) based on the prompt and criteria:
        
        PROMPT: {prompt_data.get('prompt', '')}
        STUDENT WRITING: {text}
        
        Evaluate on:
        1. Content & Ideas (0-25 points)
        2. Organization & Structure (0-25 points)
        3. Grammar & Mechanics (0-25 points)
        4. Vocabulary & Word Choice (0-25 points)
        
        Provide:
        - Scores for each category
        - Overall score (0-100)
        - Specific positive feedback
        - 2-3 areas for improvement
        - Encouragement appropriate for child's age
        
        Return as structured JSON.
        """
        
        evaluation = self.openai_client.generate_content(evaluation_prompt)
        
        # Add additional metrics
        word_count = len(text.split())
        sentence_count = len([s for s in text.split('.') if s.strip()])
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        evaluation_data = {
            'evaluation': evaluation,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_sentence_length': avg_sentence_length,
            'prompt_adherence': self.check_prompt_adherence(text, prompt_data)
        }
        
        # Complete session
        overall_score = evaluation.get('overall_score', 75)
        session.complete_session(
            score=overall_score,
            data={
                'prompt': prompt_data,
                'student_text': text,
                'evaluation': evaluation_data
            }
        )
        db.session.commit()
        
        # Update progress
        self.update_writing_progress(session.student_id, session, evaluation_data)
        
        return evaluation_data
    
    def check_prompt_adherence(self, text: str, prompt_data: Dict) -> Dict:
        prompt_text = prompt_data.get('prompt', '')
        required_elements = prompt_data.get('required_elements', [])
        
        adherence_score = 0.5  # Base score
        
        # Check if required elements are present
        elements_found = []
        for element in required_elements:
            if element.lower() in text.lower():
                elements_found.append(element)
                adherence_score += 0.1
        
        # Check word count target
        target_words = prompt_data.get('word_target', 200)
        actual_words = len(text.split())
        
        if 0.8 <= actual_words / target_words <= 1.5:  # Within reasonable range
            adherence_score += 0.2
        
        return {
            'adherence_score': min(1.0, adherence_score),
            'elements_found': elements_found,
            'word_count_match': actual_words / target_words
        }
    
    def generate_improvement_suggestions(self, student_id: int, evaluation_data: Dict) -> List[str]:
        # Generate personalized improvement suggestions
        evaluation = evaluation_data.get('evaluation', {})
        
        suggestions = []
        
        # Grammar suggestions
        grammar_score = evaluation.get('grammar_score', 75)
        if grammar_score < 70:
            suggestions.append("Practice checking your sentences for capital letters and periods")
            suggestions.append("Try reading your writing out loud to catch mistakes")
        
        # Content suggestions
        content_score = evaluation.get('content_score', 75)
        if content_score < 70:
            suggestions.append("Add more details to make your story more interesting")
            suggestions.append("Think about what the reader wants to know")
        
        # Organization suggestions
        organization_score = evaluation.get('organization_score', 75)
        if organization_score < 70:
            suggestions.append("Try organizing your ideas with a beginning, middle, and end")
            suggestions.append("Use transition words like 'first', 'then', 'finally'")
        
        # Vocabulary suggestions
        vocabulary_score = evaluation.get('vocabulary_score', 75)
        if vocabulary_score < 70:
            suggestions.append("Try using more descriptive words")
            suggestions.append("Think of different ways to say common words")
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    def update_writing_progress(self, student_id: int, session: LearningSession, evaluation_data: Dict):
        progress = Progress.query.filter_by(
            student_id=student_id,
            module_type='writing'
        ).first()
        
        if not progress:
            progress = Progress(
                student_id=student_id,
                module_type='writing'
            )
            db.session.add(progress)
        
        progress.update_from_session(session)
        
        # Analyze strengths and improvement areas
        evaluation = evaluation_data.get('evaluation', {})
        weak_areas = []
        strong_areas = []
        
        categories = {
            'content_score': 'Content & Ideas',
            'organization_score': 'Organization',
            'grammar_score': 'Grammar & Mechanics',
            'vocabulary_score': 'Vocabulary'
        }
        
        for score_key, area_name in categories.items():
            score = evaluation.get(score_key, 75)
            if score >= 85:
                strong_areas.append(area_name)
            elif score < 65:
                weak_areas.append(area_name)
        
        progress.improvement_areas = weak_areas
        progress.strengths = strong_areas
        
        db.session.commit()
    
    def get_writing_portfolio(self, student_id: int, limit: int = 10) -> List[Dict]:
        sessions = LearningSession.query.filter_by(
            student_id=student_id,
            module_type='writing',
            is_completed=True
        ).order_by(LearningSession.completed_at.desc()).limit(limit).all()
        
        portfolio = []
        for session in sessions:
            session_data = session.session_data or {}
            portfolio.append({
                'id': session.id,
                'date': session.completed_at.isoformat(),
                'prompt': session_data.get('prompt', {}).get('title', 'Writing Exercise'),
                'word_count': session_data.get('evaluation', {}).get('word_count', 0),
                'score': session.performance_score,
                'text_preview': (session_data.get('student_text', '')[:100] + '...' 
                               if len(session_data.get('student_text', '')) > 100 
                               else session_data.get('student_text', ''))
            })
        
        return portfolio
    
    def export_writing_report(self, student_id: int) -> Dict:
        # Generate comprehensive writing progress report
        progress = Progress.query.filter_by(
            student_id=student_id,
            module_type='writing'
        ).first()
        
        portfolio = self.get_writing_portfolio(student_id, 20)
        
        if not progress:
            return {'message': 'No writing progress data available'}
        
        return {
            'student_id': student_id,
            'overall_progress': progress.to_dict(),
            'writing_samples': portfolio,
            'improvement_trends': self.calculate_improvement_trends(portfolio),
            'recommendations': self.generate_improvement_suggestions(student_id, {})
        }
    
    def calculate_improvement_trends(self, portfolio: List[Dict]) -> Dict:
        if len(portfolio) < 2:
            return {'trend': 'insufficient_data'}
        
        scores = [item['score'] for item in portfolio if item['score']]
        scores.reverse()  # Chronological order
        
        if len(scores) < 2:
            return {'trend': 'no_scores'}
        
        # Simple trend calculation
        recent_avg = sum(scores[-3:]) / len(scores[-3:])
        earlier_avg = sum(scores[:3]) / len(scores[:3])
        
        if recent_avg > earlier_avg + 5:
            trend = 'improving'
        elif recent_avg < earlier_avg - 5:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'recent_average': recent_avg,
            'earlier_average': earlier_avg,
            'total_samples': len(scores)
        }