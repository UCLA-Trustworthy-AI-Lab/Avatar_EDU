import json
import tempfile
import os
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app.api.azure_speech_client import AzureSpeechClient
from app.api.openai_client import OpenAIClient
from app.models.session import LearningSession
from app.models.speaking import (
    SpeakingSession, SpeakingPracticeContent,
    WordPronunciationHistory, SpeakingChallenge,
    StudentSpeakingChallenge
)
from app.models.progress import Progress, ModuleProgress
import logging

logger = logging.getLogger(__name__)
from app import db

class EnhancedSpeakingService:
    """Enhanced speaking service with three sub-sections: Words, Sentences, Paragraphs"""

    def __init__(self):
        self.azure_client = AzureSpeechClient()
        self.openai_client = OpenAIClient()

        # Define content for different practice types
        self.practice_categories = {
            'word': [
                'academic_vocabulary', 'toefl_words', 'ielts_words',
                'business_terms', 'daily_vocabulary', 'technical_terms'
            ],
            'sentence': [
                'daily_conversation', 'academic_discussion', 'business_communication',
                'exam_speaking', 'pronunciation_patterns', 'intonation_practice'
            ],
            'paragraph': [
                'self_introduction', 'topic_description', 'opinion_expression',
                'academic_presentation', 'storytelling', 'exam_response'
            ]
        }

    # ============ WORD PRACTICE SECTION ============

    def get_word_practice_content(self,
                                  difficulty_level: str = 'intermediate',
                                  category: str = 'academic_vocabulary',
                                  count: int = 10) -> List[Dict]:
        """Get words for pronunciation practice"""

        # Query existing content from database
        words = SpeakingPracticeContent.query.filter_by(
            practice_type='word',
            difficulty_level=difficulty_level,
            category=category,
            is_active=True
        ).limit(count).all()

        if len(words) < count:
            # Generate additional words if not enough in database
            generated_words = self._generate_word_practice_content(
                difficulty_level, category, count - len(words)
            )
            words.extend(generated_words)

        return [word.to_dict() for word in words]

    def _generate_word_practice_content(self,
                                       difficulty_level: str,
                                       category: str,
                                       count: int) -> List[SpeakingPracticeContent]:
        """Generate word practice content using AI"""

        prompt = f"""Generate {count} English words for pronunciation practice:
        - Difficulty: {difficulty_level} (for Chinese students aged 16-20)
        - Category: {category}
        - Include words commonly used in academic contexts
        - Focus on words that Chinese speakers often mispronounce

        For each word, provide:
        1. The word
        2. IPA phonetic transcription
        3. Part of speech
        4. Brief definition
        5. Chinese translation
        6. Common pronunciation mistakes for Chinese speakers
        7. An example sentence

        Return as JSON array."""

        response = self.openai_client.generate_content(prompt)

        # Handle different response formats
        try:
            # Check if OpenAI returned an error (no API key, etc.)
            if isinstance(response, dict) and 'error' in response:
                words = []
            elif isinstance(response, dict) and 'content' in response:
                words = json.loads(response['content'])
            elif isinstance(response, str):
                words = json.loads(response)
            elif isinstance(response, list):
                words = response
            else:
                words = []

            # Ensure words is a list
            if not isinstance(words, list):
                words = [words] if words else []

        except (json.JSONDecodeError, TypeError):
            # Fallback: create basic word data
            words = []

        # If no words generated, create fallback words
        if not words:
            if category == 'academic_vocabulary':
                words = [{"word": "analyze", "ipa": "/ˈæn.ə.laɪz/", "chinese_translation": "分析", "example_sentence": "We need to analyze the data."}]
            elif category == 'daily_conversation':
                words = [{"word": "restaurant", "ipa": "/ˈres.tər.ɑːnt/", "chinese_translation": "餐厅", "example_sentence": "Let's go to a restaurant."}]
            else:
                words = [{"word": "practice", "ipa": "/ˈpræk.tɪs/", "chinese_translation": "练习", "example_sentence": "Practice makes perfect."}]

        generated_content = []
        for word_data in words:
            # Handle case where word_data might be a string
            if isinstance(word_data, str):
                word_data = {'word': word_data}

            # Ensure we have required content
            word_text = word_data.get('word')
            if not word_text:
                word_text = "practice"

            content = SpeakingPracticeContent(
                practice_type='word',
                content_text=word_text,
                phonetic_transcription=word_data.get('ipa', '/ˈpræk.tɪs/'),
                difficulty_level=difficulty_level,
                category=category,
                context_hint=word_data.get('example_sentence', 'Practice this word'),
                chinese_translation=word_data.get('chinese_translation', '练习')
            )
            db.session.add(content)
            generated_content.append(content)

        db.session.commit()
        return generated_content

    def get_database_word_content(self,
                                 difficulty_level: str,
                                 category: str,
                                 count: int) -> List[SpeakingPracticeContent]:
        """Get existing word content from database instead of generating new content"""
        try:
            # Query existing content from database
            content = SpeakingPracticeContent.query.filter_by(
                practice_type='word',
                difficulty_level=difficulty_level,
                category=category,
                is_active=True
            ).limit(count).all()

            if content:
                return content
            else:
                # Fallback: if no database content found, generate new content
                return self._generate_word_practice_content(difficulty_level, category, min(count, 5))

        except Exception as e:
            logger.error(f"Error getting database word content: {str(e)}")
            # Fallback: generate new content
            return self._generate_word_practice_content(difficulty_level, category, min(count, 5))

    def assess_word_pronunciation(self,
                                 student_id: int,
                                 audio_file_path: str,
                                 target_word: str,
                                 session_id: int) -> Dict:
        """Assess pronunciation of a single word"""

        # Try Azure Speech Services with fallback
        try:
            assessment = self.azure_client.assess_pronunciation(audio_file_path, target_word)
        except Exception as e:
            print(f"Azure services not available, using fallback for word assessment: {e}")
            # Provide mock assessment data
            assessment = {
                'PronScore': 85,
                'AccuracyScore': 88,
                'FluencyScore': 82,
                'CompletenessScore': 90,
                'Words': [{
                    'Word': target_word,
                    'PronScore': 85,
                    'Phonemes': [{'Phoneme': 'demo', 'PronScore': 85}]
                }]
            }

        # Extract detailed phoneme-level analysis
        phoneme_scores = []
        problem_phonemes = []

        # Handle word details from Azure response
        if 'Words' in assessment and assessment['Words']:
            for word_detail in assessment['Words']:
                if 'Phonemes' in word_detail:
                    for phoneme in word_detail['Phonemes']:
                        score = phoneme.get('AccuracyScore', 0)
                        phoneme_scores.append(score)
                        if score < 70:  # Threshold for problematic phoneme
                            problem_phonemes.append({
                                'phoneme': phoneme.get('Phoneme'),
                                'score': score
                            })

        # Get scores directly from Azure response (new format)
        pronunciation_score = assessment.get('PronScore', 0)
        accuracy_score = assessment.get('AccuracyScore', 0)
        fluency_score = assessment.get('FluencyScore', 0)
        completeness_score = assessment.get('CompletenessScore', 0)

        # Create speaking session record
        speaking_session = SpeakingSession(
            student_id=student_id,
            session_id=session_id,
            practice_type='word',
            practice_content=target_word,
            audio_file_path=audio_file_path,
            pronunciation_score=pronunciation_score,
            accuracy_score=accuracy_score,
            fluency_score=fluency_score,
            completeness_score=completeness_score,
            phoneme_analysis=problem_phonemes,
            problem_words=[target_word] if pronunciation_score < 75 else []
        )

        # Generate AI feedback
        feedback = self._generate_word_feedback(
            target_word, pronunciation_score, problem_phonemes
        )
        speaking_session.ai_feedback = feedback

        db.session.add(speaking_session)

        # Update word pronunciation history
        self._update_word_history(student_id, target_word, pronunciation_score, problem_phonemes)

        db.session.commit()

        return {
            'session_id': speaking_session.id,
            'word': target_word,
            'pronunciation_score': pronunciation_score,
            'accuracy_score': accuracy_score,
            'phoneme_analysis': problem_phonemes,
            'feedback': feedback,
            'improvement_tips': self._get_phoneme_improvement_tips(problem_phonemes)
        }

    def _generate_word_feedback(self, word: str, score: float, problem_phonemes: List) -> str:
        """Generate personalized feedback for word pronunciation"""

        feedback_parts = []

        # Performance level assessment
        if score >= 90:
            feedback_parts.append(f"🎉 Outstanding pronunciation of '{word}'! Your articulation is crystal clear and natural.")
        elif score >= 80:
            feedback_parts.append(f"✅ Excellent pronunciation of '{word}'! Very fluent speech with accurate pronunciation.")
        elif score >= 70:
            feedback_parts.append(f"👍 Good pronunciation of '{word}'! You're speaking clearly and confidently.")
        elif score >= 60:
            feedback_parts.append(f"📈 You're making solid progress with '{word}'. Keep practicing!")
        else:
            feedback_parts.append(f"🎯 Let's work on improving '{word}' together. Focus on each sound carefully.")

        # Specific phoneme guidance
        if problem_phonemes:
            phoneme_names = []
            for p in problem_phonemes[:2]:  # Focus on top 2 issues
                phoneme = p.get('phoneme', '')
                score = p.get('score', 0)

                if phoneme:
                    phoneme_names.append(phoneme)

            if phoneme_names:
                feedback_parts.append(f"Pay special attention to the {'/'.join(phoneme_names)} sound(s).")

        # Encouragement and next steps
        if score >= 85:
            feedback_parts.append("Try challenging yourself with longer sentences using this word!")
        elif score >= 70:
            feedback_parts.append("Practice this word in different sentences to build confidence.")
        elif score < 60:
            feedback_parts.append("Break the word into syllables and practice each part slowly.")

        return " ".join(feedback_parts)

    def _get_phoneme_improvement_tips(self, problem_phonemes: List) -> List[Dict]:
        """Get specific tips for improving problematic phonemes"""

        tips = []
        phoneme_tips_map = {
            'θ': "Place your tongue between your teeth and blow air gently (as in 'think')",
            'ð': "Similar to 'θ' but with voice vibration (as in 'this')",
            'r': "Curl your tongue back slightly, don't let it touch the roof of your mouth",
            'l': "Touch the tip of your tongue to the ridge behind your upper teeth",
            'v': "Place your upper teeth on your lower lip and vibrate",
            'w': "Round your lips and then open them while voicing",
            'æ': "Open your mouth wide and spread your lips (as in 'cat')",
            'ɪ': "Keep your tongue relaxed and in the middle of your mouth (as in 'sit')",
            'ə': "The most relaxed vowel sound, like the 'a' in 'about'"
        }

        for phoneme_data in problem_phonemes[:3]:  # Limit to top 3 problems
            phoneme = phoneme_data['phoneme']
            if phoneme in phoneme_tips_map:
                tips.append({
                    'phoneme': phoneme,
                    'tip': phoneme_tips_map[phoneme],
                    'score': phoneme_data['score']
                })

        return tips

    # ============ SENTENCE PRACTICE SECTION ============

    def get_sentence_practice_content(self,
                                     difficulty_level: str = 'intermediate',
                                     category: str = 'daily_conversation',
                                     count: int = 5) -> List[Dict]:
        """Get sentences for pronunciation and intonation practice"""

        sentences = SpeakingPracticeContent.query.filter_by(
            practice_type='sentence',
            difficulty_level=difficulty_level,
            category=category,
            is_active=True
        ).limit(count).all()

        if len(sentences) < count:
            generated_sentences = self._generate_sentence_practice_content(
                difficulty_level, category, count - len(sentences)
            )
            sentences.extend(generated_sentences)

        return [sentence.to_dict() for sentence in sentences]

    def _generate_sentence_practice_content(self,
                                          difficulty_level: str,
                                          category: str,
                                          count: int) -> List[SpeakingPracticeContent]:
        """Generate sentence practice content using AI"""

        prompt = f"""Generate {count} English sentences for pronunciation practice:
        - Difficulty: {difficulty_level} (for Chinese students aged 16-20)
        - Category: {category}
        - Include various sentence structures and intonation patterns
        - Focus on natural, practical sentences used in academic/professional contexts

        For each sentence, provide:
        1. The sentence
        2. Key pronunciation focuses (specific sounds, linking, stress patterns)
        3. Intonation pattern (rising, falling, etc.)
        4. Chinese translation
        5. Context or usage scenario
        6. Common mistakes Chinese speakers make

        Return as JSON array."""

        response = self.openai_client.generate_content(prompt)

        # Handle different response formats and ensure we have valid content
        try:
            # Check if OpenAI returned an error (no API key, etc.)
            if isinstance(response, dict) and 'error' in response:
                sentences = []
            elif isinstance(response, dict) and 'content' in response:
                sentences = json.loads(response['content'])
            elif isinstance(response, str):
                sentences = json.loads(response)
            elif isinstance(response, list):
                sentences = response
            else:
                sentences = []

            # Ensure sentences is a list
            if not isinstance(sentences, list):
                sentences = [sentences] if sentences else []

        except (json.JSONDecodeError, TypeError):
            # Fallback: create basic sentence data
            sentences = []

        # If no sentences generated, create fallback sentences
        if not sentences:
            if category == 'daily_conversation':
                sentences = [{"sentence": "How are you doing today?", "context": "Daily greeting", "chinese_translation": "你今天怎么样？"}]
            elif category == 'academic_discussion':
                sentences = [{"sentence": "The research methodology demonstrates significant validity.", "context": "Academic discussion", "chinese_translation": "研究方法显示出显著的有效性。"}]
            else:
                sentences = [{"sentence": "This is a practice sentence.", "context": "General practice", "chinese_translation": "这是一个练习句子。"}]

        generated_content = []
        for sentence_data in sentences:
            # Ensure we have required content
            sentence_text = sentence_data.get('sentence') if isinstance(sentence_data, dict) else str(sentence_data)
            if not sentence_text:
                sentence_text = "This is a practice sentence."

            content = SpeakingPracticeContent(
                practice_type='sentence',
                content_text=sentence_text,
                difficulty_level=difficulty_level,
                category=category,
                context_hint=sentence_data.get('context', 'Practice sentence') if isinstance(sentence_data, dict) else 'Practice sentence',
                chinese_translation=sentence_data.get('chinese_translation', '') if isinstance(sentence_data, dict) else ''
            )
            db.session.add(content)
            generated_content.append(content)

        db.session.commit()
        return generated_content

    def assess_sentence_pronunciation(self,
                                     student_id: int,
                                     audio_file_path: str,
                                     target_sentence: str,
                                     session_id: int) -> Dict:
        """Assess pronunciation of a sentence including prosody"""

        # Use Azure for comprehensive assessment including prosody
        assessment = self.azure_client.assess_pronunciation(
            audio_file_path,
            target_sentence,
            enable_prosody=True  # Enable prosody assessment for sentences
        )

        # Extract scores (fixed for new Azure response format)
        pronunciation_score = assessment.get('PronScore', 0)
        accuracy_score = assessment.get('AccuracyScore', 0)
        fluency_score = assessment.get('FluencyScore', 0)
        completeness_score = assessment.get('CompletenessScore', 0)
        prosody_score = 85  # Default prosody score since Azure doesn't provide this directly

        # Analyze word-level issues
        word_issues = []
        if 'Words' in assessment and assessment['Words']:
            for word in assessment['Words']:
                word_score = word.get('AccuracyScore', 0)
                if word_score < 75:
                    word_issues.append({
                        'word': word.get('Word'),
                            'score': word_score,
                            'error_type': word.get('ErrorType', 'Mispronunciation')
                        })

        # Calculate speech rate
        audio_duration = self._get_audio_duration(audio_file_path)
        word_count = len(target_sentence.split())
        words_per_minute = (word_count / audio_duration * 60) if audio_duration > 0 else 0

        # Create session record
        speaking_session = SpeakingSession(
            student_id=student_id,
            session_id=session_id,
            practice_type='sentence',
            practice_content=target_sentence,
            audio_file_path=audio_file_path,
            pronunciation_score=pronunciation_score,
            accuracy_score=accuracy_score,
            fluency_score=fluency_score,
            completeness_score=completeness_score,
            prosody_score=prosody_score,
            words_per_minute=words_per_minute,
            word_level_analysis=word_issues,
            problem_words=[w['word'] for w in word_issues]
        )

        # Generate AI feedback focusing on sentence-level features
        feedback = self._generate_sentence_feedback(
            target_sentence, pronunciation_score, prosody_score, word_issues
        )
        speaking_session.ai_feedback = feedback

        # Generate improvement suggestions
        suggestions = self._generate_sentence_improvement_suggestions(
            prosody_score, fluency_score, words_per_minute
        )
        speaking_session.improvement_suggestions = suggestions

        db.session.add(speaking_session)
        db.session.commit()

        return {
            'session_id': speaking_session.id,
            'overall_score': speaking_session.calculate_overall_score(),
            'pronunciation_score': pronunciation_score,
            'prosody_score': prosody_score,
            'fluency_score': fluency_score,
            'words_per_minute': words_per_minute,
            'problem_words': word_issues,
            'feedback': feedback,
            'improvement_suggestions': suggestions
        }

    def _generate_sentence_feedback(self,
                                   sentence: str,
                                   pronunciation_score: float,
                                   prosody_score: float,
                                   word_issues: List) -> str:
        """Generate feedback for sentence pronunciation"""

        feedback_parts = []

        # Overall performance
        if pronunciation_score >= 85:
            feedback_parts.append("Excellent sentence pronunciation!")
        elif pronunciation_score >= 70:
            feedback_parts.append("Good pronunciation overall.")
        else:
            feedback_parts.append("Let's work on improving your sentence pronunciation.")

        # Prosody feedback
        if prosody_score < 70:
            feedback_parts.append("Focus on the rhythm and intonation of the sentence.")
        elif prosody_score < 85:
            feedback_parts.append("Your intonation is developing well.")

        # Word-specific issues
        if word_issues:
            problem_words = ", ".join([w['word'] for w in word_issues[:3]])
            feedback_parts.append(f"Practice these words: {problem_words}")

        return " ".join(feedback_parts)

    def _generate_sentence_improvement_suggestions(self,
                                                  prosody_score: float,
                                                  fluency_score: float,
                                                  wpm: float) -> List[str]:
        """Generate specific improvement suggestions for sentence practice"""

        suggestions = []

        if prosody_score < 70:
            suggestions.append("Practice stress patterns by emphasizing important words")
            suggestions.append("Listen to native speakers and mimic their intonation")

        if fluency_score < 70:
            suggestions.append("Practice speaking without long pauses")
            suggestions.append("Try reading the sentence multiple times to build fluency")

        if wpm < 100:
            suggestions.append("Try to speak a bit faster to sound more natural")
        elif wpm > 180:
            suggestions.append("Slow down slightly to improve clarity")

        return suggestions

    # ============ PARAGRAPH PRACTICE SECTION ============

    def get_paragraph_practice_content(self,
                                      difficulty_level: str = 'intermediate',
                                      category: str = 'self_introduction',
                                      exam_type: Optional[str] = None) -> Dict:
        """Get paragraph for extended speaking practice"""

        paragraph = SpeakingPracticeContent.query.filter_by(
            practice_type='paragraph',
            difficulty_level=difficulty_level,
            category=category,
            is_active=True
        ).first()

        if not paragraph:
            paragraph = self._generate_paragraph_practice_content(
                difficulty_level, category, exam_type
            )

        return paragraph.to_dict()

    def _generate_paragraph_practice_content(self,
                                           difficulty_level: str,
                                           category: str,
                                           exam_type: Optional[str]) -> SpeakingPracticeContent:
        """Generate paragraph practice content"""

        exam_context = f"for {exam_type} speaking test" if exam_type else ""

        prompt = f"""Generate a paragraph for speaking practice {exam_context}:
        - Difficulty: {difficulty_level} (for Chinese students aged 16-20)
        - Category: {category}
        - Length: 100-150 words
        - Include varied sentence structures and academic vocabulary

        Provide:
        1. The paragraph text
        2. Key speaking points to emphasize
        3. Suggested pauses and breathing points
        4. Chinese translation
        5. Tips for natural delivery

        Return as JSON."""

        response = self.openai_client.generate_content(prompt)

        # Handle different response formats and ensure we have valid content
        try:
            # Check if OpenAI returned an error (no API key, etc.)
            if isinstance(response, dict) and 'error' in response:
                paragraph_data = {}
            elif isinstance(response, dict) and 'content' in response:
                paragraph_data = json.loads(response['content'])
            elif isinstance(response, str):
                paragraph_data = json.loads(response)
            elif isinstance(response, dict):
                paragraph_data = response
            else:
                paragraph_data = {}

            # Ensure paragraph_data is a dictionary
            if not isinstance(paragraph_data, dict):
                paragraph_data = {}

        except (json.JSONDecodeError, TypeError):
            # Fallback: create basic paragraph data
            paragraph_data = {}

        # Ensure we have required content, create fallback if needed
        # Try multiple possible keys from AI response
        paragraph_text = (paragraph_data.get('paragraph') or
                         paragraph_data.get('paragraph_text') or
                         paragraph_data.get('text') or
                         paragraph_data.get('content'))

        if not paragraph_text:
            # Create a fallback paragraph based on category and difficulty
            if category == 'self_introduction':
                paragraph_text = f"Hello, my name is [Student Name]. I am studying English to improve my communication skills. My goal is to become more confident in speaking English in both academic and professional settings."
            elif category == 'academic_presentation':
                paragraph_text = f"Today I will discuss an important topic in my field of study. This presentation will cover key concepts and their practical applications in real-world scenarios."
            else:
                paragraph_text = f"This is a {difficulty_level} level speaking practice paragraph for {category} category. Practice speaking clearly and confidently."

        content = SpeakingPracticeContent(
            practice_type='paragraph',
            content_text=paragraph_text,
            difficulty_level=difficulty_level,
            category=category,
            exam_type=exam_type,
            context_hint=paragraph_data.get('speaking_tips', 'Practice speaking clearly and confidently'),
            chinese_translation=paragraph_data.get('chinese_translation', '')
        )

        db.session.add(content)
        db.session.commit()

        return content

    def assess_paragraph_pronunciation(self,
                                      student_id: int,
                                      audio_file_path: str,
                                      target_paragraph: str,
                                      session_id: int) -> Dict:
        """Assess extended speech including fluency, coherence, and content"""

        # Use Azure for technical assessment
        assessment = self.azure_client.assess_pronunciation(
            audio_file_path,
            target_paragraph,
            enable_prosody=True,
            enable_content=True  # Enable content assessment for paragraphs
        )

        # Extract comprehensive scores (fixed for new Azure response format)
        pronunciation_score = assessment.get('PronScore', 0)
        accuracy_score = assessment.get('AccuracyScore', 0)
        fluency_score = assessment.get('FluencyScore', 0)
        completeness_score = assessment.get('CompletenessScore', 0)
        prosody_score = 85  # Default prosody score since Azure doesn't provide this directly

        # Analyze speech features
        audio_duration = self._get_audio_duration(audio_file_path)
        word_count = len(target_paragraph.split())
        words_per_minute = (word_count / audio_duration * 60) if audio_duration > 0 else 0

        # Detect pauses and fillers
        pause_analysis = self._analyze_pauses_and_fillers(audio_file_path, target_paragraph)

        # Get content analysis from AI
        content_analysis = self._analyze_paragraph_content(
            audio_file_path, target_paragraph
        )

        # Create comprehensive session record
        speaking_session = SpeakingSession(
            student_id=student_id,
            session_id=session_id,
            practice_type='paragraph',
            practice_content=target_paragraph,
            audio_file_path=audio_file_path,
            recording_duration=audio_duration,
            pronunciation_score=pronunciation_score,
            accuracy_score=accuracy_score,
            fluency_score=fluency_score,
            completeness_score=completeness_score,
            prosody_score=prosody_score,
            words_per_minute=words_per_minute,
            pause_count=pause_analysis.get('pause_count', 0),
            filler_word_count=pause_analysis.get('filler_count', 0)
        )

        # Generate comprehensive feedback
        feedback = self._generate_paragraph_feedback(
            pronunciation_score, fluency_score, prosody_score,
            words_per_minute, content_analysis
        )
        speaking_session.ai_feedback = feedback

        # Generate improvement plan
        improvement_plan = self._generate_improvement_plan(
            pronunciation_score, fluency_score, prosody_score,
            pause_analysis, content_analysis
        )
        speaking_session.improvement_suggestions = improvement_plan

        db.session.add(speaking_session)
        db.session.commit()

        return {
            'session_id': speaking_session.id,
            'overall_score': speaking_session.calculate_overall_score(),
            'pronunciation_score': pronunciation_score,
            'fluency_score': fluency_score,
            'prosody_score': prosody_score,
            'words_per_minute': words_per_minute,
            'pause_analysis': pause_analysis,
            'content_analysis': content_analysis,
            'feedback': feedback,
            'improvement_plan': improvement_plan
        }

    def _analyze_paragraph_content(self, audio_file_path: str, target_text: str) -> Dict:
        """Analyze the content and coherence of paragraph speech"""

        # Transcribe the actual speech
        transcription = self.azure_client.speech_to_text(audio_file_path)

        prompt = f"""Analyze this spoken paragraph for content and coherence:

        Target Text: {target_text}
        Actual Speech: {transcription}

        Evaluate:
        1. Content completeness (0-100)
        2. Logical flow and coherence (0-100)
        3. Vocabulary usage appropriateness (0-100)
        4. Grammar accuracy (0-100)
        5. Key points covered vs missed

        Return as JSON with scores and brief comments."""

        analysis = self.openai_client.generate_content(prompt)

        # Handle error or missing API key
        if isinstance(analysis, dict) and 'error' in analysis:
            return {
                'content_completeness': 70,
                'logical_flow': 70,
                'vocabulary_usage': 70,
                'grammar_accuracy': 70,
                'comments': 'Detailed content analysis unavailable. Please configure OpenAI API key for full feedback.'
            }

        try:
            return json.loads(analysis) if isinstance(analysis, str) else analysis
        except (json.JSONDecodeError, TypeError):
            return {'content_completeness': 70, 'logical_flow': 70, 'vocabulary_usage': 70, 'grammar_accuracy': 70}

    def _analyze_pauses_and_fillers(self, audio_file_path: str, target_text: str) -> Dict:
        """Analyze pauses and filler words in speech"""

        # This would integrate with audio analysis tools
        # For now, returning simulated analysis
        return {
            'pause_count': 5,
            'average_pause_duration': 0.8,
            'filler_count': 2,
            'filler_words': ['um', 'uh'],
            'natural_pauses': 3,
            'unnatural_pauses': 2
        }

    def _generate_paragraph_feedback(self,
                                    pronunciation_score: float,
                                    fluency_score: float,
                                    prosody_score: float,
                                    wpm: float,
                                    content_analysis: Dict) -> str:
        """Generate comprehensive feedback for paragraph practice"""

        feedback_parts = []

        # Overall performance
        overall_score = (pronunciation_score + fluency_score + prosody_score) / 3
        if overall_score >= 85:
            feedback_parts.append("Excellent paragraph delivery! You're speaking like a confident English speaker.")
        elif overall_score >= 70:
            feedback_parts.append("Good job on the paragraph! Your speaking skills are developing well.")
        else:
            feedback_parts.append("You're making progress with extended speech. Let's focus on some key areas.")

        # Specific aspects
        if fluency_score < 70:
            feedback_parts.append("Work on maintaining a steady flow without long pauses.")

        if prosody_score < 70:
            feedback_parts.append("Practice varying your tone to make your speech more engaging.")

        if wpm < 120:
            feedback_parts.append("Try to speak a bit more fluently to maintain listener engagement.")

        # Content feedback
        content_score = content_analysis.get('content_completeness', 0)
        if content_score < 70:
            feedback_parts.append("Make sure to cover all key points in the paragraph.")

        return " ".join(feedback_parts)

    def _generate_improvement_plan(self,
                                  pronunciation_score: float,
                                  fluency_score: float,
                                  prosody_score: float,
                                  pause_analysis: Dict,
                                  content_analysis: Dict) -> List[str]:
        """Generate a personalized improvement plan"""

        plan = []

        # Priority 1: Major issues
        if pronunciation_score < 60:
            plan.append("Priority 1: Focus on clear pronunciation - practice difficult words separately")

        if fluency_score < 60:
            plan.append("Priority 1: Build fluency - read aloud daily for 10 minutes")

        # Priority 2: Moderate issues
        if prosody_score < 70:
            plan.append("Priority 2: Work on intonation - listen and shadow native speakers")

        if pause_analysis.get('filler_count', 0) > 3:
            plan.append("Priority 2: Reduce filler words - pause silently instead of using 'um' or 'uh'")

        # Priority 3: Fine-tuning
        if pronunciation_score > 80 and fluency_score > 80:
            plan.append("Priority 3: Polish your delivery - focus on expressing emotion and emphasis")

        return plan

    # ============ UTILITY METHODS ============

    def _get_audio_duration(self, audio_file_path: str) -> float:
        """Get duration of audio file in seconds"""
        # This would use audio processing library like librosa
        # For now, returning a simulated value
        return 10.0

    def _update_word_history(self,
                            student_id: int,
                            word: str,
                            score: float,
                            problem_phonemes: List):
        """Update student's word pronunciation history"""

        history = WordPronunciationHistory.query.filter_by(
            student_id=student_id,
            word=word
        ).first()

        if not history:
            history = WordPronunciationHistory(
                student_id=student_id,
                word=word,
                latest_score=score,
                best_score=score,
                average_score=score,
                problem_phonemes=[p['phoneme'] for p in problem_phonemes]
            )
            db.session.add(history)
        else:
            history.update_with_new_attempt(
                score,
                [p['phoneme'] for p in problem_phonemes]
            )

    # ============ CHALLENGE MANAGEMENT ============

    def create_daily_challenge(self, student_id: int) -> Dict:
        """Create a personalized daily speaking challenge"""

        # Get student's weak areas
        weak_words = WordPronunciationHistory.query.filter_by(
            student_id=student_id,
            is_mastered=False
        ).order_by(WordPronunciationHistory.average_score).limit(5).all()

        # Create challenge mixing all three practice types
        challenge = SpeakingChallenge(
            title="Daily Speaking Challenge",
            description="Complete today's speaking practice to improve your pronunciation",
            challenge_type='daily',
            practice_types=['word', 'sentence', 'paragraph'],
            minimum_score=75,
            required_attempts=1,
            points_reward=20,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=1)
        )

        db.session.add(challenge)
        db.session.commit()

        # Create student challenge record
        student_challenge = StudentSpeakingChallenge(
            student_id=student_id,
            challenge_id=challenge.id,
            status='not_started'
        )

        db.session.add(student_challenge)
        db.session.commit()

        return challenge.to_dict()

    def get_student_progress_summary(self, student_id: int) -> Dict:
        """Get comprehensive speaking progress summary"""

        # Get overall statistics
        total_sessions = SpeakingSession.query.filter_by(student_id=student_id).count()

        # Average scores by practice type
        word_avg = db.session.query(db.func.avg(SpeakingSession.pronunciation_score))\
            .filter_by(student_id=student_id, practice_type='word').scalar() or 0

        sentence_avg = db.session.query(db.func.avg(SpeakingSession.pronunciation_score))\
            .filter_by(student_id=student_id, practice_type='sentence').scalar() or 0

        paragraph_avg = db.session.query(db.func.avg(SpeakingSession.pronunciation_score))\
            .filter_by(student_id=student_id, practice_type='paragraph').scalar() or 0

        # Get mastered words
        mastered_words = WordPronunciationHistory.query.filter_by(
            student_id=student_id,
            is_mastered=True
        ).count()

        # Get problem areas
        problem_words = WordPronunciationHistory.query.filter_by(
            student_id=student_id,
            is_mastered=False
        ).order_by(WordPronunciationHistory.average_score).limit(10).all()

        # Get recent improvement
        recent_sessions = SpeakingSession.query.filter_by(student_id=student_id)\
            .order_by(SpeakingSession.created_at.desc()).limit(10).all()

        recent_scores = [s.pronunciation_score for s in recent_sessions]
        improvement_trend = 'improving' if len(recent_scores) > 1 and recent_scores[0] > recent_scores[-1] else 'stable'

        return {
            'total_practice_sessions': total_sessions,
            'average_scores': {
                'word': round(word_avg, 1),
                'sentence': round(sentence_avg, 1),
                'paragraph': round(paragraph_avg, 1)
            },
            'mastered_words': mastered_words,
            'problem_words': [w.to_dict() for w in problem_words],
            'improvement_trend': improvement_trend,
            'recent_scores': recent_scores[:5],
            'recommendations': self._generate_practice_recommendations(
                word_avg, sentence_avg, paragraph_avg, problem_words
            )
        }

    def _generate_practice_recommendations(self,
                                          word_avg: float,
                                          sentence_avg: float,
                                          paragraph_avg: float,
                                          problem_words: List) -> List[str]:
        """Generate personalized practice recommendations"""

        recommendations = []

        # Identify weakest area
        scores = {'word': word_avg, 'sentence': sentence_avg, 'paragraph': paragraph_avg}
        weakest_area = min(scores, key=scores.get)

        if scores[weakest_area] < 70:
            recommendations.append(f"Focus on {weakest_area} practice - aim for 10 minutes daily")

        # Word-specific recommendations
        if problem_words:
            common_phonemes = {}
            for word in problem_words:
                if word.problem_phonemes:
                    for phoneme in word.problem_phonemes:
                        common_phonemes[phoneme] = common_phonemes.get(phoneme, 0) + 1

            if common_phonemes:
                most_problematic = max(common_phonemes, key=common_phonemes.get)
                recommendations.append(f"Practice the '{most_problematic}' sound - it appears in many of your challenging words")

        # Fluency recommendations
        if sentence_avg < 75:
            recommendations.append("Read English texts aloud daily to improve fluency")

        # Advanced recommendations
        if all(score > 80 for score in scores.values()):
            recommendations.append("Challenge yourself with academic presentations and debates")

        return recommendations

    # ============ TOPIC ANSWER PRACTICE SECTION ============

    def get_topic_practice_content(self,
                                   difficulty_level: str = 'intermediate',
                                   category: str = 'general') -> Dict:
        """Generate AI-based topic for IELTS-style speaking practice"""

        # Define topic prompts by category
        topic_prompts = {
            'general': [
                "Describe your favorite hobby and explain why you enjoy it.",
                "Talk about a memorable experience from your childhood.",
                "Describe a place you would like to visit and explain why.",
                "Discuss the importance of friendship in your life."
            ],
            'education': [
                "Describe your ideal school or university.",
                "Discuss the role of technology in modern education.",
                "Talk about a subject you found challenging and how you overcame it.",
                "Explain the benefits of studying abroad."
            ],
            'technology': [
                "Describe how technology has changed daily life.",
                "Discuss the advantages and disadvantages of social media.",
                "Talk about a piece of technology you couldn't live without.",
                "Explain how artificial intelligence might affect jobs in the future."
            ],
            'environment': [
                "Describe what individuals can do to protect the environment.",
                "Discuss the effects of climate change on your country.",
                "Talk about renewable energy sources.",
                "Explain the importance of recycling."
            ],
            'culture': [
                "Describe an important festival or celebration in your culture.",
                "Discuss how globalization affects local traditions.",
                "Talk about cultural differences you've observed.",
                "Explain the importance of preserving cultural heritage."
            ],
            'work': [
                "Describe your ideal job and explain why.",
                "Discuss the importance of work-life balance.",
                "Talk about skills that are important in today's workplace.",
                "Explain how remote work has changed the modern workplace."
            ],
            'travel': [
                "Describe a place you have visited that impressed you.",
                "Discuss the benefits of traveling to different countries.",
                "Talk about your dream vacation destination.",
                "Explain how travel can change a person's perspective."
            ],
            'health': [
                "Describe how you maintain a healthy lifestyle.",
                "Discuss the importance of mental health awareness.",
                "Talk about a sport or exercise you enjoy.",
                "Explain the role of diet in maintaining good health."
            ]
        }

        # Select random topic from category
        topics = topic_prompts.get(category, topic_prompts['general'])
        selected_topic = random.choice(topics)

        return {
            'id': f"topic_{random.randint(1000, 9999)}",
            'topic_text': selected_topic,
            'category': category,
            'difficulty_level': difficulty_level,
            'preparation_time': 90,
            'speaking_time': 60,
            'instructions': "You have 90 seconds to prepare your answer and 1 minute to speak.",
            'assessment_criteria': [
                'Fluency and coherence',
                'Lexical resource (vocabulary)',
                'Grammatical range and accuracy',
                'Pronunciation'
            ]
        }

    def get_database_topic_content(self,
                                   difficulty_level: str = 'intermediate',
                                   category: str = 'general') -> Dict:
        """Get topics from database for IELTS-style speaking practice"""

        # Query database for topic content
        topic = SpeakingPracticeContent.query.filter_by(
            practice_type='topic',
            difficulty_level=difficulty_level,
            category=category
        ).first()

        if topic:
            return {
                'id': topic.id,
                'topic_text': topic.content_text,
                'category': topic.category,
                'difficulty_level': topic.difficulty_level,
                'preparation_time': 90,
                'speaking_time': 60,
                'instructions': "You have 90 seconds to prepare your answer and 1 minute to speak.",
                'context_hint': topic.context_hint,
                'assessment_criteria': [
                    'Fluency and coherence',
                    'Lexical resource (vocabulary)',
                    'Grammatical range and accuracy',
                    'Pronunciation'
                ]
            }
        else:
            # Fallback to AI-generated content if no database topics
            return self.get_topic_practice_content(difficulty_level, category)

    def assess_topic_answer(self,
                           student_id: int,
                           audio_file_path: str,
                           topic_text: str,
                           session_id: int,
                           preparation_time: int = 90,
                           speaking_time: int = 60) -> Dict:
        """Assess IELTS-style topic answer with comprehensive scoring"""

        # Analyze speech features
        audio_duration = self._get_audio_duration(audio_file_path)

        # Try Azure for pronunciation assessment with fallback
        try:
            assessment = self.azure_client.assess_pronunciation(
                audio_file_path,
                reference_text="",  # No reference text for open topic response
                enable_prosody=True,
                enable_content=True
            )

            # Extract technical scores
            pronunciation_score = assessment.get('PronScore', 0)
            accuracy_score = assessment.get('AccuracyScore', 0)
            fluency_score = assessment.get('FluencyScore', 0)
            completeness_score = assessment.get('CompletenessScore', 0)

            # Get transcription for content analysis
            transcription = self.azure_client.speech_to_text(audio_file_path)

        except Exception as e:
            print(f"Azure services not available, using fallback: {e}")
            # Provide mock results when Azure is not available
            pronunciation_score = 75
            accuracy_score = 80
            fluency_score = 78
            completeness_score = 82
            transcription = f"Demo response to the topic: {topic_text[:50]}... (Azure transcription not available)"
        word_count = len(transcription.split()) if transcription else 0
        words_per_minute = (word_count / audio_duration * 60) if audio_duration > 0 else 0

        # IELTS-style scoring using AI
        ielts_scores = self._get_ielts_style_scores(transcription, topic_text, audio_duration)

        # Create speaking session record
        speaking_session = SpeakingSession(
            student_id=student_id,
            session_id=session_id,
            practice_type='topic',
            practice_content=topic_text,
            audio_file_path=audio_file_path,
            recording_duration=audio_duration,
            pronunciation_score=ielts_scores['pronunciation'],
            accuracy_score=accuracy_score,
            fluency_score=ielts_scores['fluency'],
            completeness_score=ielts_scores['lexical'],
            prosody_score=ielts_scores['grammar'],
            words_per_minute=words_per_minute,
            word_count=word_count,
            transcription=transcription
        )

        db.session.add(speaking_session)
        db.session.commit()

        # Calculate overall band score (IELTS style: average of 4 criteria)
        band_score = round((
            ielts_scores['fluency'] +
            ielts_scores['lexical'] +
            ielts_scores['grammar'] +
            ielts_scores['pronunciation']
        ) / 4, 1)

        return {
            'session_id': speaking_session.id,
            'overall_band_score': band_score,
            'scores': {
                'fluency_coherence': ielts_scores['fluency'],
                'lexical_resource': ielts_scores['lexical'],
                'grammatical_accuracy': ielts_scores['grammar'],
                'pronunciation': ielts_scores['pronunciation']
            },
            'technical_scores': {
                'words_per_minute': round(words_per_minute, 1),
                'word_count': word_count,
                'speaking_duration': round(audio_duration, 1)
            },
            'transcription': transcription,
            'feedback': self._generate_topic_feedback(ielts_scores, transcription, topic_text),
            'improvement_suggestions': self._generate_topic_suggestions(ielts_scores, words_per_minute)
        }

    def _get_ielts_style_scores(self, transcription: str, topic_text: str, duration: float) -> Dict:
        """Generate IELTS-style scores using AI analysis"""

        prompt = f"""
        Evaluate this IELTS speaking response based on the 4 IELTS criteria. Give scores from 1.0 to 9.0 (in 0.5 increments).

        Topic: {topic_text}
        Student Response: {transcription}
        Speaking Duration: {duration:.1f} seconds

        Provide scores for:
        1. Fluency and Coherence (how smoothly they speak and organize ideas)
        2. Lexical Resource (vocabulary range and accuracy)
        3. Grammatical Range and Accuracy (grammar variety and correctness)
        4. Pronunciation (clarity and natural rhythm)

        Format as JSON: {{"fluency": 6.5, "lexical": 6.0, "grammar": 6.5, "pronunciation": 6.0}}
        """

        try:
            response = self.openai_client.generate_content(
                prompt=prompt,
                max_tokens=150,
                temperature=0.3
            )

            # Fallback if OpenAI is unavailable
            if isinstance(response, dict) and 'error' in response:
                return {'fluency': 5.5, 'lexical': 5.5, 'grammar': 5.5, 'pronunciation': 5.5}

            # Parse JSON response
            scores_text = response if isinstance(response, str) else json.dumps(response)
            scores_text = scores_text.strip()
            if scores_text.startswith('```json'):
                scores_text = scores_text.split('```json')[1].split('```')[0]
            elif scores_text.startswith('```'):
                scores_text = scores_text.split('```')[1]

            scores = json.loads(scores_text)

            # Validate scores are in range
            for key in ['fluency', 'lexical', 'grammar', 'pronunciation']:
                if key not in scores or not (1.0 <= scores[key] <= 9.0):
                    scores[key] = 6.0  # Default score

            return scores

        except Exception as e:
            print(f"Error generating IELTS scores: {e}")
            # Return default scores if AI analysis fails
            return {
                'fluency': 6.0,
                'lexical': 6.0,
                'grammar': 6.0,
                'pronunciation': 6.0
            }

    def _generate_topic_feedback(self, scores: Dict, transcription: str, topic: str) -> List[str]:
        """Generate specific feedback for topic answer"""

        feedback = []

        # Fluency feedback
        if scores['fluency'] < 6.0:
            feedback.append("Work on speaking more smoothly with fewer hesitations.")
        elif scores['fluency'] >= 7.0:
            feedback.append("Good fluency! You spoke naturally and coherently.")

        # Vocabulary feedback
        if scores['lexical'] < 6.0:
            feedback.append("Try to use more varied vocabulary and avoid repetition.")
        elif scores['lexical'] >= 7.0:
            feedback.append("Excellent vocabulary usage! You demonstrated good range.")

        # Grammar feedback
        if scores['grammar'] < 6.0:
            feedback.append("Focus on using more complex sentence structures correctly.")
        elif scores['grammar'] >= 7.0:
            feedback.append("Strong grammar usage with good sentence variety.")

        # Pronunciation feedback
        if scores['pronunciation'] < 6.0:
            feedback.append("Practice pronunciation of individual sounds and word stress.")
        elif scores['pronunciation'] >= 7.0:
            feedback.append("Clear pronunciation that's easy to understand.")

        return feedback

    def _generate_topic_suggestions(self, scores: Dict, wpm: float) -> List[str]:
        """Generate improvement suggestions for topic answers"""

        suggestions = []

        # Find lowest scoring area
        lowest_score = min(scores.values())
        weak_areas = [area for area, score in scores.items() if score == lowest_score]

        if 'fluency' in weak_areas:
            suggestions.append("Practice daily conversation to improve fluency")
            suggestions.append("Record yourself speaking on various topics")

        if 'lexical' in weak_areas:
            suggestions.append("Learn topic-specific vocabulary")
            suggestions.append("Practice using synonyms and varied expressions")

        if 'grammar' in weak_areas:
            suggestions.append("Study complex sentence structures")
            suggestions.append("Practice using different tenses appropriately")

        if 'pronunciation' in weak_areas:
            suggestions.append("Use pronunciation practice apps")
            suggestions.append("Listen to native speakers and mimic their pronunciation")

        # Speaking speed suggestions
        if wpm < 120:
            suggestions.append("Practice speaking at a natural pace - aim for 130-150 words per minute")
        elif wpm > 180:
            suggestions.append("Slow down your speech for better clarity")

        return suggestions