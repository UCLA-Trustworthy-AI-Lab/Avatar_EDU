import requests
import logging
from flask import current_app
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class WordsAPIClient:
    """Client for interacting with WordsAPI for vocabulary definitions and data"""
    
    def __init__(self):
        self.base_url = "https://wordsapiv1.p.rapidapi.com/words"
        self.headers = {
            "X-RapidAPI-Key": current_app.config.get('WORDSAPI_KEY'),
            "X-RapidAPI-Host": "wordsapiv1.p.rapidapi.com"
        }
    
    def get_word_details(self, word: str) -> Optional[Dict]:
        """
        Get comprehensive word details including definitions, pronunciation, examples
        
        Args:
            word: The word to look up
            
        Returns:
            Dictionary containing word details or None if not found
        """
        try:
            url = f"{self.base_url}/{word.lower()}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Process and structure the response
                word_data = {
                    'word': data.get('word', word),
                    'definitions': self._extract_definitions(data.get('results', [])),
                    'pronunciation': data.get('pronunciation', {}),
                    'syllables': data.get('syllables', {}),
                    'frequency': data.get('frequency'),
                    'examples': self._extract_examples(data.get('results', [])),
                    'synonyms': self._extract_synonyms(data.get('results', [])),
                    'antonyms': self._extract_antonyms(data.get('results', []))
                }
                
                return word_data
                
            elif response.status_code == 404:
                logger.warning(f"Word '{word}' not found in WordsAPI")
                return None
            else:
                logger.error(f"WordsAPI error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling WordsAPI for word '{word}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_word_details: {e}")
            return None
    
    def get_word_definitions(self, word: str) -> List[Dict]:
        """
        Get just the definitions for a word
        
        Args:
            word: The word to look up
            
        Returns:
            List of definition dictionaries
        """
        try:
            url = f"{self.base_url}/{word.lower()}/definitions"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('definitions', [])
            else:
                logger.warning(f"Could not get definitions for '{word}': {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting definitions for '{word}': {e}")
            return []
    
    def get_word_examples(self, word: str) -> List[str]:
        """
        Get usage examples for a word
        
        Args:
            word: The word to look up
            
        Returns:
            List of example sentences
        """
        try:
            url = f"{self.base_url}/{word.lower()}/examples"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('examples', [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting examples for '{word}': {e}")
            return []
    
    def get_word_synonyms(self, word: str) -> List[str]:
        """
        Get synonyms for a word
        
        Args:
            word: The word to look up
            
        Returns:
            List of synonym words
        """
        try:
            url = f"{self.base_url}/{word.lower()}/synonyms"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('synonyms', [])
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting synonyms for '{word}': {e}")
            return []
    
    def get_word_pronunciation(self, word: str) -> Dict:
        """
        Get pronunciation data for a word
        
        Args:
            word: The word to look up
            
        Returns:
            Dictionary with pronunciation information
        """
        try:
            url = f"{self.base_url}/{word.lower()}/pronunciation"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('pronunciation', {})
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error getting pronunciation for '{word}': {e}")
            return {}
    
    def _extract_definitions(self, results: List[Dict]) -> List[Dict]:
        """Extract and format definitions from WordsAPI results"""
        definitions = []
        for result in results:
            if 'definition' in result:
                definitions.append({
                    'definition': result['definition'],
                    'part_of_speech': result.get('partOfSpeech', ''),
                    'synonyms': result.get('synonyms', []),
                    'antonyms': result.get('antonyms', []),
                    'examples': result.get('examples', [])
                })
        return definitions
    
    def _extract_examples(self, results: List[Dict]) -> List[str]:
        """Extract examples from WordsAPI results"""
        examples = []
        for result in results:
            if 'examples' in result:
                examples.extend(result['examples'])
        return list(set(examples))  # Remove duplicates
    
    def _extract_synonyms(self, results: List[Dict]) -> List[str]:
        """Extract synonyms from WordsAPI results"""
        synonyms = []
        for result in results:
            if 'synonyms' in result:
                synonyms.extend(result['synonyms'])
        return list(set(synonyms))  # Remove duplicates
    
    def _extract_antonyms(self, results: List[Dict]) -> List[str]:
        """Extract antonyms from WordsAPI results"""
        antonyms = []
        for result in results:
            if 'antonyms' in result:
                antonyms.extend(result['antonyms'])
        return list(set(antonyms))  # Remove duplicates
    
    def estimate_word_difficulty(self, word_data: Dict) -> int:
        """
        Estimate word difficulty level (1-10) based on various factors
        
        Args:
            word_data: Word data from get_word_details
            
        Returns:
            Difficulty level from 1 (easy) to 10 (very hard)
        """
        try:
            difficulty = 5  # Default middle difficulty
            
            # Adjust based on frequency (if available)
            frequency = word_data.get('frequency')
            if frequency:
                if frequency > 5:
                    difficulty -= 2  # Very common word
                elif frequency > 3:
                    difficulty -= 1  # Common word
                elif frequency < 1:
                    difficulty += 2  # Rare word
            
            # Adjust based on syllable count
            syllables = word_data.get('syllables', {})
            syllable_count = syllables.get('count', 0)
            if syllable_count > 4:
                difficulty += 1
            elif syllable_count > 6:
                difficulty += 2
            
            # Adjust based on number of definitions (complex words have more definitions)
            definitions = word_data.get('definitions', [])
            if len(definitions) > 5:
                difficulty += 1
            
            # Ensure difficulty is within bounds
            difficulty = max(1, min(10, difficulty))
            
            return difficulty
            
        except Exception as e:
            logger.error(f"Error estimating word difficulty: {e}")
            return 5  # Default to medium difficulty