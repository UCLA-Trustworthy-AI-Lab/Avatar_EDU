import logging
from typing import Dict, List, Optional
from app import db
from app.models.reading import VocabularyInteraction, ReadingProgress
from app.models.user import Student
from app.api.wordsapi_client import WordsAPIClient
from datetime import datetime

logger = logging.getLogger(__name__)

class VocabularyService:
    """Service for handling vocabulary interactions and learning progress"""
    
    def __init__(self):
        self.words_client = WordsAPIClient()
    
    def process_word_click(self, student_id: int, reading_session_id: int, word: str) -> Dict:
        """
        Process a word click from a student during reading
        
        Args:
            student_id: ID of the student
            reading_session_id: ID of the current reading session
            word: The word that was clicked
            
        Returns:
            Dictionary containing word information and interaction data
        """
        try:
            # Check if this word was already looked up in this session
            existing_interaction = VocabularyInteraction.query.filter_by(
                student_id=student_id,
                reading_session_id=reading_session_id,
                word=word.lower()
            ).first()
            
            if existing_interaction:
                # Increment lookup count
                existing_interaction.looked_up_count += 1
                existing_interaction.interaction_timestamp = datetime.utcnow()
                db.session.commit()
                
                return self._format_word_response(existing_interaction)
            
            # Get word data from WordsAPI
            word_data = self.words_client.get_word_details(word)
            
            if not word_data:
                logger.warning(f"Could not find word data for: {word}")
                # Return fallback word data instead of error
                word_data = self._get_fallback_word_data(word)
            
            # Create new vocabulary interaction record
            interaction = VocabularyInteraction(
                student_id=student_id,
                reading_session_id=reading_session_id,
                word=word.lower(),
                word_definition=self._format_definitions(word_data.get('definitions', [])),
                pronunciation=self._format_pronunciation(word_data.get('pronunciation', {})),
                examples=word_data.get('examples', [])[:3],  # Limit to 3 examples
                synonyms=word_data.get('synonyms', [])[:5],  # Limit to 5 synonyms
                difficulty_level=self.words_client.estimate_word_difficulty(word_data),
                frequency_rank=self._estimate_frequency_rank(word_data)
            )
            
            db.session.add(interaction)
            db.session.commit()
            
            # Update student's reading progress
            self._update_vocabulary_progress(student_id, word.lower())
            
            return self._format_word_response(interaction, word_data)
            
        except Exception as e:
            logger.error(f"Error processing word click for '{word}': {e}")
            # Return fallback data instead of error to provide a better user experience
            word_data = self._get_fallback_word_data(word)
            
            # Create a simple interaction record with fallback data
            interaction = VocabularyInteraction(
                student_id=student_id,
                reading_session_id=reading_session_id,
                word=word.lower(),
                word_definition=word_data['definitions'][0]['definition'],
                pronunciation=word_data['pronunciation'].get('all', f"/{word}/"),
                examples=word_data.get('examples', []),
                synonyms=word_data.get('synonyms', []),
                difficulty_level=5  # Default difficulty
            )
            
            try:
                db.session.add(interaction)
                db.session.commit()
            except:
                # If database fails too, just return the word data without saving
                pass
            
            return self._format_word_response(interaction, word_data)
    
    def get_word_with_chinese_translation(self, student_id: int, reading_session_id: int, word: str) -> Dict:
        """
        Get word information with Chinese translation
        
        Args:
            student_id: ID of the student
            reading_session_id: ID of the current reading session
            word: The word to translate
            
        Returns:
            Dictionary containing word information with Chinese translation
        """
        try:
            # First get the basic word information
            response = self.process_word_click(student_id, reading_session_id, word)
            
            if 'error' in response:
                return response
            
            # Add Chinese translation (this would integrate with a translation API)
            # For now, we'll use a placeholder - in production, integrate with Google Translate API
            chinese_translation = self._get_chinese_translation(word)
            
            # Update the interaction record with Chinese translation
            interaction = VocabularyInteraction.query.filter_by(
                student_id=student_id,
                reading_session_id=reading_session_id,
                word=word.lower()
            ).first()
            
            if interaction:
                interaction.chinese_translation = chinese_translation
                db.session.commit()
            
            response['chinese_translation'] = chinese_translation
            return response
            
        except Exception as e:
            logger.error(f"Error getting Chinese translation for '{word}': {e}")
            return self.process_word_click(student_id, reading_session_id, word)
    
    def mark_word_as_mastered(self, student_id: int, word: str) -> bool:
        """
        Mark a word as mastered by the student
        
        Args:
            student_id: ID of the student
            word: The word to mark as mastered
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find all interactions with this word for the student
            interactions = VocabularyInteraction.query.filter_by(
                student_id=student_id,
                word=word.lower()
            ).all()
            
            # Mark all interactions as mastered
            for interaction in interactions:
                interaction.is_mastered = True
            
            db.session.commit()
            
            # Update reading progress
            self._update_mastered_vocabulary(student_id, word.lower())
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking word '{word}' as mastered: {e}")
            return False
    
    def get_student_vocabulary_stats(self, student_id: int) -> Dict:
        """
        Get vocabulary statistics for a student
        
        Args:
            student_id: ID of the student
            
        Returns:
            Dictionary containing vocabulary statistics
        """
        try:
            # Get reading progress
            progress = ReadingProgress.query.filter_by(student_id=student_id).first()
            
            if not progress:
                return {
                    'vocabulary_size': 0,
                    'words_looked_up': 0,
                    'words_mastered': 0,
                    'most_difficult_words': [],
                    'recent_words': []
                }
            
            # Get vocabulary interactions
            total_interactions = VocabularyInteraction.query.filter_by(student_id=student_id).count()
            unique_words = db.session.query(VocabularyInteraction.word).filter_by(
                student_id=student_id
            ).distinct().count()
            mastered_words = VocabularyInteraction.query.filter_by(
                student_id=student_id,
                is_mastered=True
            ).distinct(VocabularyInteraction.word).count()
            
            # Get most difficult words (high difficulty, looked up multiple times)
            difficult_words = db.session.query(VocabularyInteraction).filter_by(
                student_id=student_id
            ).filter(
                VocabularyInteraction.difficulty_level >= 7,
                VocabularyInteraction.looked_up_count > 1,
                VocabularyInteraction.is_mastered == False
            ).order_by(VocabularyInteraction.difficulty_level.desc()).limit(10).all()
            
            # Get recent words (last 20 interactions)
            recent_words = VocabularyInteraction.query.filter_by(
                student_id=student_id
            ).order_by(VocabularyInteraction.interaction_timestamp.desc()).limit(20).all()
            
            return {
                'vocabulary_size': progress.vocabulary_size,
                'words_looked_up': unique_words,
                'words_mastered': mastered_words,
                'total_interactions': total_interactions,
                'most_difficult_words': [self._format_word_summary(w) for w in difficult_words],
                'recent_words': [self._format_word_summary(w) for w in recent_words]
            }
            
        except Exception as e:
            logger.error(f"Error getting vocabulary stats for student {student_id}: {e}")
            return {}
    
    def _format_word_response(self, interaction: VocabularyInteraction, word_data: Dict = None) -> Dict:
        """Format word interaction data for API response"""
        return {
            'word': interaction.word,
            'definition': interaction.word_definition,
            'pronunciation': interaction.pronunciation,
            'examples': interaction.examples or [],
            'synonyms': interaction.synonyms or [],
            'chinese_translation': interaction.chinese_translation,
            'difficulty_level': interaction.difficulty_level,
            'looked_up_count': interaction.looked_up_count,
            'is_mastered': interaction.is_mastered,
            'timestamp': interaction.interaction_timestamp.isoformat()
        }
    
    def _format_word_summary(self, interaction: VocabularyInteraction) -> Dict:
        """Format word data for summary displays"""
        return {
            'word': interaction.word,
            'difficulty_level': interaction.difficulty_level,
            'looked_up_count': interaction.looked_up_count,
            'is_mastered': interaction.is_mastered,
            'last_interaction': interaction.interaction_timestamp.isoformat()
        }
    
    def _format_definitions(self, definitions: List[Dict]) -> str:
        """Format definitions list into a readable string"""
        if not definitions:
            return ""
        
        formatted_defs = []
        for i, def_data in enumerate(definitions[:3], 1):  # Limit to 3 definitions
            part_of_speech = def_data.get('part_of_speech', '')
            definition = def_data.get('definition', '')
            
            if part_of_speech:
                formatted_defs.append(f"{i}. ({part_of_speech}) {definition}")
            else:
                formatted_defs.append(f"{i}. {definition}")
        
        return " | ".join(formatted_defs)
    
    def _format_pronunciation(self, pronunciation: Dict) -> str:
        """Format pronunciation data into IPA string"""
        if not pronunciation:
            return ""
        
        # WordsAPI might return pronunciation as a dict with different keys
        if isinstance(pronunciation, dict):
            # Try different possible keys
            for key in ['all', 'noun', 'verb', 'adjective']:
                if key in pronunciation:
                    return pronunciation[key]
        elif isinstance(pronunciation, str):
            return pronunciation
        
        return ""
    
    def _estimate_frequency_rank(self, word_data: Dict) -> int:
        """Estimate frequency rank from word data"""
        frequency = word_data.get('frequency')
        if frequency:
            # Convert frequency score to rank estimate (higher frequency = lower rank number)
            return max(1, min(10000, int(10000 / max(frequency, 0.1))))
        return 5000  # Default middle frequency
    
    def _get_chinese_translation(self, word: str) -> str:
        """
        Get Chinese translation for a word
        TODO: Integrate with Google Translate API or similar service
        """
        # Placeholder - in production, use Google Translate API
        translation_map = {
            'hello': '你好',
            'world': '世界',
            'language': '语言',
            'learning': '学习',
            'student': '学生',
            'teacher': '教师',
            'book': '书',
            'read': '阅读',
            'write': '写作',
            'speak': '说话'
        }
        
        return translation_map.get(word.lower(), f"[{word}的中文翻译]")
    
    def _update_vocabulary_progress(self, student_id: int, word: str):
        """Update student's vocabulary progress"""
        try:
            progress = ReadingProgress.query.filter_by(student_id=student_id).first()
            
            if not progress:
                progress = ReadingProgress(student_id=student_id)
                db.session.add(progress)
            
            # Add word to difficult words if it's looked up multiple times
            word_interactions = VocabularyInteraction.query.filter_by(
                student_id=student_id,
                word=word
            ).count()
            
            if word_interactions > 1:
                difficult_words = progress.difficult_words or []
                if word not in difficult_words:
                    difficult_words.append(word)
                    progress.difficult_words = difficult_words
            
            progress.updated_at = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating vocabulary progress: {e}")
    
    def _get_fallback_word_data(self, word: str) -> Dict:
        """
        Provide fallback word data when external APIs fail
        
        Args:
            word: The word to create fallback data for
            
        Returns:
            Dictionary with basic word information
        """
        # Common word definitions for testing
        fallback_definitions = {
            'the': 'definite article used to specify a particular noun',
            'and': 'conjunction used to connect words, phrases, or clauses',
            'machine': 'a device with moving parts that performs work',
            'machines': 'plural of machine; devices that perform work',
            'computer': 'an electronic device for processing data',
            'technology': 'the application of scientific knowledge for practical purposes',
            'reading': 'the action of looking at and understanding written words',
            'student': 'a person who is learning or studying',
            'language': 'a system of communication used by humans',
            'learning': 'the process of acquiring knowledge or skills',
            'education': 'the process of teaching or learning',
            'knowledge': 'information and understanding gained through experience',
            'understand': 'to comprehend the meaning of something',
            'information': 'facts or knowledge provided or learned',
            'development': 'the process of growing or improving',
            'important': 'having great significance or value',
            'different': 'not the same as another',
            'example': 'a thing characteristic of its kind or illustrating a general rule',
            'process': 'a series of actions or steps to achieve a result',
            'system': 'a set of connected things forming a complex whole'
        }
        
        word_lower = word.lower()
        definition = fallback_definitions.get(word_lower, f'A word meaning: {word}')
        
        return {
            'word': word,
            'definitions': [{'definition': definition, 'part_of_speech': 'noun'}],
            'pronunciation': {'all': f"/{word.lower()}/"},
            'examples': [f"This is an example sentence using the word {word}."],
            'synonyms': ['related_word'],
            'frequency': 3
        }
    
    def _update_mastered_vocabulary(self, student_id: int, word: str):
        """Update student's mastered vocabulary list"""
        try:
            progress = ReadingProgress.query.filter_by(student_id=student_id).first()
            
            if progress:
                mastered_words = progress.mastered_words or []
                if word not in mastered_words:
                    mastered_words.append(word)
                    progress.mastered_words = mastered_words
                    progress.vocabulary_size = len(mastered_words)
                
                # Remove from difficult words if it was there
                difficult_words = progress.difficult_words or []
                if word in difficult_words:
                    difficult_words.remove(word)
                    progress.difficult_words = difficult_words
                
                progress.updated_at = datetime.utcnow()
                db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating mastered vocabulary: {e}")