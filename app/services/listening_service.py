import requests
import json
from typing import Dict, List, Optional
from app.api.heygen_client import HeyGenClient
from app.api.openai_client import OpenAIClient
from app.models.session import LearningSession
from app.models.progress import Progress
from app import db

class ListeningService:
    def __init__(self):
        self.heygen_client = HeyGenClient()
        self.openai_client = OpenAIClient()
    
    def create_listening_session(self, student_id: int, topic: str = None) -> LearningSession:
        session = LearningSession(
            student_id=student_id,
            module_type='listening',
            activity_type='avatar_story'
        )
        db.session.add(session)
        db.session.commit()
        return session
    
    def generate_avatar_content(self, topic: str, difficulty_level: str = 'intermediate') -> Dict:
        prompt = f"""
        Create a {difficulty_level} level story about {topic} suitable for English learners aged 16-20.
        The story should be:
        - 2-3 minutes when spoken
        - Engaging and educational
        - Academic-level vocabulary
        - Include 3-5 key learning points

        Return the story text and key points for comprehension questions.
        """

        story_content = self.openai_client.generate_content(prompt)

        # Check if OpenAI returned an error
        if isinstance(story_content, dict) and 'error' in story_content:
            return {
                'story': f'A short passage about {topic}. This is a placeholder because AI services are not available. Please configure your OpenAI API key in .env for generated content.',
                'key_points': ['Main topic understanding', 'Detail comprehension'],
                'difficulty_level': difficulty_level
            }

        story_text = story_content.get('story') or story_content.get('content') or story_content.get('story_text') or f'A passage about {topic}.'
        key_points = story_content.get('key_points', ['Main topic understanding', 'Detail comprehension'])

        return {
            'story': story_text,
            'key_points': key_points,
            'difficulty_level': difficulty_level
        }
    
    def generate_comprehension_questions(self, story_content: str, num_questions: int = 5) -> List[Dict]:
        prompt = f"""
        Create {num_questions} comprehension questions for this story suitable for students aged 16-20:
        
        {story_content}
        
        Questions should:
        - Test understanding, not memorization
        - Be multiple choice with 4 options
        - Include easy, medium, and challenging questions
        - Be engaging and age-appropriate
        
        Return as JSON with question, options, correct_answer, and difficulty.
        """
        
        questions = self.openai_client.generate_content(prompt)

        # Fallback if OpenAI is unavailable
        if isinstance(questions, dict) and 'error' in questions:
            return [
                {
                    'question': 'What was the main topic of the story?',
                    'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                    'correct_answer': 'Option A',
                    'difficulty': 'medium'
                }
            ]

        return questions
    
    def evaluate_comprehension(self, session_id: int, answers: List[str]) -> Dict:
        session = LearningSession.query.get(session_id)
        if not session:
            return {'error': 'Session not found'}
        
        questions = session.session_data.get('questions', [])
        if len(answers) != len(questions):
            return {'error': 'Answer count mismatch'}
        
        correct_count = 0
        detailed_results = []
        
        for i, (question, answer) in enumerate(zip(questions, answers)):
            is_correct = answer == question['correct_answer']
            if is_correct:
                correct_count += 1
            
            detailed_results.append({
                'question_id': i,
                'question': question['question'],
                'student_answer': answer,
                'correct_answer': question['correct_answer'],
                'is_correct': is_correct,
                'difficulty': question.get('difficulty', 'medium')
            })
        
        score = (correct_count / len(questions)) * 100
        
        # Update session
        session.complete_session(
            score=score,
            data={
                'questions': questions,
                'answers': answers,
                'detailed_results': detailed_results
            }
        )
        db.session.commit()
        
        # Update progress
        self.update_student_progress(session.student_id, session, detailed_results)
        
        return {
            'score': score,
            'correct_count': correct_count,
            'total_questions': len(questions),
            'detailed_results': detailed_results
        }
    
    def update_student_progress(self, student_id: int, session: LearningSession, results: List[Dict]):
        progress = Progress.query.filter_by(
            student_id=student_id,
            module_type='listening'
        ).first()
        
        if not progress:
            progress = Progress(
                student_id=student_id,
                module_type='listening'
            )
            db.session.add(progress)
        
        progress.update_from_session(session)
        
        # Analyze improvement areas
        weak_areas = []
        strong_areas = []
        
        for result in results:
            if not result['is_correct'] and result['difficulty'] in ['easy', 'medium']:
                weak_areas.append(f"Story comprehension - {result['difficulty']} level")
            elif result['is_correct'] and result['difficulty'] == 'challenging':
                strong_areas.append("Advanced comprehension")
        
        progress.improvement_areas = weak_areas
        progress.strengths = strong_areas
        
        db.session.commit()
    
    def get_session_history(self, student_id: int, limit: int = 10) -> List[Dict]:
        sessions = LearningSession.query.filter_by(
            student_id=student_id,
            module_type='listening'
        ).order_by(LearningSession.started_at.desc()).limit(limit).all()
        
        return [session.to_dict() for session in sessions]