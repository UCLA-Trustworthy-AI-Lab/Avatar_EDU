import json
import tempfile
from typing import Dict, List, Optional
from app.api.azure_speech_client import AzureSpeechClient
from app.api.openai_client import OpenAIClient
from app.models.session import LearningSession
from app.models.progress import Progress, ModuleProgress
from app import db

class SpeakingService:
    def __init__(self):
        self.azure_client = AzureSpeechClient()
        self.openai_client = OpenAIClient()
    
    def create_speaking_session(self, student_id: int, activity_type: str = 'pronunciation') -> LearningSession:
        session = LearningSession(
            student_id=student_id,
            module_type='speaking',
            activity_type=activity_type
        )
        db.session.add(session)
        db.session.commit()
        return session
    
    def generate_pronunciation_exercise(self, difficulty_level: str = 'intermediate') -> Dict:
        prompt = f"""
        Create a pronunciation exercise for students aged 16-20 at {difficulty_level} level.
        Include:
        - 10 words/phrases to practice
        - Phonetic guides
        - Common pronunciation challenges
        - Target sounds to focus on
        
        Return structured data with words, phonetics, and tips.
        """
        
        exercise = self.openai_client.generate_content(prompt)

        # Fallback if OpenAI is unavailable
        if isinstance(exercise, dict) and 'error' in exercise:
            return {
                'words': ['hello', 'world', 'language', 'practice', 'speaking',
                          'learning', 'reading', 'writing', 'listening', 'vocabulary'],
                'phonetics': ['/həˈloʊ/', '/wɜːrld/', '/ˈlæŋɡwɪdʒ/', '/ˈpræktɪs/', '/ˈspiːkɪŋ/',
                              '/ˈlɜːrnɪŋ/', '/ˈriːdɪŋ/', '/ˈraɪtɪŋ/', '/ˈlɪsənɪŋ/', '/voʊˈkæbjəˌlɛri/'],
                'tips': ['Focus on clear pronunciation', 'Practice at a comfortable pace'],
                'message': 'Configure your OpenAI API key in .env for personalized exercises.'
            }

        return exercise
    
    def analyze_pronunciation(self, audio_file_path: str, target_text: str) -> Dict:
        # Use Azure Speech Services for pronunciation assessment
        pronunciation_result = self.azure_client.assess_pronunciation(
            audio_file_path, 
            target_text
        )
        
        # Extract key metrics
        accuracy_score = pronunciation_result.get('AccuracyScore', 0)
        fluency_score = pronunciation_result.get('FluencyScore', 0)
        completeness_score = pronunciation_result.get('CompletenessScore', 0)
        
        overall_score = (accuracy_score + fluency_score + completeness_score) / 3
        
        # Analyze specific issues
        word_issues = []
        for word_result in pronunciation_result.get('Words', []):
            if word_result.get('AccuracyScore', 100) < 80:
                word_issues.append({
                    'word': word_result.get('Word'),
                    'accuracy': word_result.get('AccuracyScore'),
                    'error_type': word_result.get('ErrorType'),
                    'phonemes': word_result.get('Phonemes', [])
                })
        
        return {
            'overall_score': overall_score,
            'accuracy_score': accuracy_score,
            'fluency_score': fluency_score,
            'completeness_score': completeness_score,
            'word_issues': word_issues,
            'feedback': self.generate_pronunciation_feedback(overall_score, word_issues)
        }
    
    def generate_pronunciation_feedback(self, score: float, word_issues: List[Dict]) -> str:
        if score >= 90:
            feedback = "Excellent pronunciation! Your speech is clear and accurate."
        elif score >= 75:
            feedback = "Good pronunciation! Here are some areas to focus on:"
        elif score >= 60:
            feedback = "Your pronunciation is developing well. Let's work on these areas:"
        else:
            feedback = "Let's practice together to improve your pronunciation:"
        
        if word_issues:
            feedback += "\n\nSpecific improvements:"
            for issue in word_issues[:3]:  # Limit to top 3 issues
                feedback += f"\n- Practice the word '{issue['word']}' - focus on clarity"
        
        return feedback
    
    def speech_to_text_analysis(self, audio_file_path: str) -> Dict:
        # Convert speech to text using Azure or OpenAI Whisper
        transcription = self.azure_client.speech_to_text(audio_file_path)
        
        # Analyze the transcription for language patterns
        analysis_prompt = f"""
        Analyze this student's speech transcription for:
        - Grammar usage
        - Vocabulary level
        - Sentence structure
        - Areas for improvement
        
        Transcription: {transcription}
        
        Provide constructive feedback for a student aged 16-20.
        """
        
        analysis = self.openai_client.generate_content(analysis_prompt)

        # Fallback if OpenAI is unavailable
        if isinstance(analysis, dict) and 'error' in analysis:
            analysis = {
                'grammar': 'Analysis not available without OpenAI API key.',
                'vocabulary_level': 'unknown',
                'feedback': 'Configure your OpenAI API key in .env for detailed speech analysis.'
            }

        return {
            'transcription': transcription,
            'analysis': analysis,
            'word_count': len(transcription.split()),
            'estimated_fluency': self.calculate_fluency_score(transcription)
        }
    
    def calculate_fluency_score(self, transcription: str) -> float:
        words = transcription.split()
        
        # Simple fluency metrics
        word_count = len(words)
        avg_word_length = sum(len(word) for word in words) / max(word_count, 1)
        unique_words = len(set(words))
        vocabulary_diversity = unique_words / max(word_count, 1)
        
        # Basic scoring algorithm
        fluency_score = min(100, (word_count * 2) + (avg_word_length * 5) + (vocabulary_diversity * 30))
        return fluency_score
    
    def complete_speaking_session(self, session_id: int, results: Dict) -> Dict:
        session = LearningSession.query.get(session_id)
        if not session:
            return {'error': 'Session not found'}
        
        # Calculate overall session score
        if 'overall_score' in results:
            session_score = results['overall_score']
        elif 'estimated_fluency' in results:
            session_score = results['estimated_fluency']
        else:
            session_score = 70  # Default score
        
        session.complete_session(
            score=session_score,
            data=results
        )
        db.session.commit()
        
        # Update progress
        self.update_speaking_progress(session.student_id, session, results)
        
        return {
            'session_id': session_id,
            'score': session_score,
            'feedback': results.get('feedback', 'Great work on your speaking practice!')
        }
    
    def update_speaking_progress(self, student_id: int, session: LearningSession, results: Dict):
        progress = Progress.query.filter_by(
            student_id=student_id,
            module_type='speaking'
        ).first()
        
        if not progress:
            progress = Progress(
                student_id=student_id,
                module_type='speaking'
            )
            db.session.add(progress)
        
        progress.update_from_session(session)
        
        # Update specific skill areas
        if 'word_issues' in results and results['word_issues']:
            # Track pronunciation issues
            pronunciation_progress = ModuleProgress.query.filter_by(
                student_id=student_id,
                module_type='speaking',
                skill_area='pronunciation'
            ).first()
            
            if not pronunciation_progress:
                pronunciation_progress = ModuleProgress(
                    student_id=student_id,
                    module_type='speaking',
                    skill_area='pronunciation'
                )
                db.session.add(pronunciation_progress)
            
            # Mark as needing attention if accuracy is low
            accuracy = results.get('accuracy_score', 100)
            if accuracy < 75:
                pronunciation_progress.needs_attention = True
                pronunciation_progress.priority_level = 5 if accuracy < 50 else 3
        
        db.session.commit()
    
    def get_speaking_progress_summary(self, student_id: int) -> Dict:
        progress = Progress.query.filter_by(
            student_id=student_id,
            module_type='speaking'
        ).first()
        
        if not progress:
            return {'message': 'No speaking progress yet'}
        
        module_progress = ModuleProgress.query.filter_by(
            student_id=student_id,
            module_type='speaking'
        ).all()
        
        return {
            'overall_progress': progress.to_dict(),
            'skill_areas': [skill.skill_area for skill in module_progress],
            'areas_needing_attention': [
                skill.skill_area for skill in module_progress 
                if skill.needs_attention
            ]
        }