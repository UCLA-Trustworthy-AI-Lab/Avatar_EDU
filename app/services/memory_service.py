"""
Memory Service - Acts like a teacher's mental model of each student.

This service:
1. Tracks mistakes and patterns across all learning sessions
2. Compresses session data into meaningful insights
3. Influences content generation (questions, topics, difficulty)
4. Provides personalized adaptive learning

Key Concept: Just like a human teacher remembers "John struggles with passive voice"
or "Mary keeps forgetting these 5 words", this system maintains a memory board
for each student across all modules.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from app import db
from app.models.memory import (
    StudentMemoryBoard, ReadingMemoryInsight, ListeningMemoryInsight,
    SpeakingMemoryInsight, WritingMemoryInsight, ConversationMemoryInsight
)
from app.models.reading import ReadingSession, VocabularyInteraction, ReadingResponse
import logging

logger = logging.getLogger(__name__)


class MemoryService:
    """Core service for managing student learning memory across all modules"""

    # Compression thresholds
    COMPRESSION_THRESHOLD = 5  # Compress after N new insights
    MAX_UNCOMPRESSED_INSIGHTS = 10  # Force compression if exceeded

    def __init__(self):
        pass

    def get_or_create_memory_board(self, student_id: int) -> StudentMemoryBoard:
        """Get existing memory board or create new one for student"""
        memory_board = StudentMemoryBoard.query.filter_by(student_id=student_id).first()

        if not memory_board:
            memory_board = StudentMemoryBoard(
                student_id=student_id,
                reading_memory={},
                listening_memory={},
                speaking_memory={},
                writing_memory={},
                conversation_memory={},
                overall_patterns={}
            )
            db.session.add(memory_board)
            db.session.commit()
            logger.info(f"Created new memory board for student {student_id}")

        return memory_board

    def get_reading_memory(self, student_id: int) -> Dict:
        """
        Get compressed reading memory for a student.
        Returns a dict with vocabulary gaps, comprehension weaknesses, etc.
        """
        memory_board = self.get_or_create_memory_board(student_id)
        return memory_board.reading_memory or {}

    def should_compress_reading_memory(self, student_id: int) -> bool:
        """Check if it's time to compress reading insights"""
        memory_board = self.get_or_create_memory_board(student_id)

        # Count uncompressed insights
        uncompressed_count = ReadingMemoryInsight.query.filter_by(
            student_id=student_id,
            is_compressed=False
        ).count()

        # Compress if threshold reached
        return uncompressed_count >= self.COMPRESSION_THRESHOLD

    def extract_reading_session_insights(
        self,
        student_id: int,
        reading_session_id: int
    ) -> ReadingMemoryInsight:
        """
        Extract insights from a completed reading session.
        This is called at the END of each reading session.

        Returns a ReadingMemoryInsight object with all the mistakes and patterns.
        """
        session = ReadingSession.query.get(reading_session_id)
        if not session:
            raise ValueError(f"Reading session {reading_session_id} not found")

        # Gather vocabulary mistakes
        vocab_interactions = VocabularyInteraction.query.filter_by(
            student_id=student_id,
            reading_session_id=reading_session_id
        ).all()

        vocabulary_mistakes = []
        difficult_words = []
        repeated_lookups = []

        for interaction in vocab_interactions:
            word_data = {
                "word": interaction.word,
                "difficulty": interaction.difficulty_level,
                "lookup_count": interaction.looked_up_count
            }
            vocabulary_mistakes.append(word_data)

            # High difficulty or multiple lookups = difficult word
            if interaction.difficulty_level and interaction.difficulty_level > 7:
                difficult_words.append(word_data)

            # Check if this word was looked up in previous sessions
            previous_lookups = VocabularyInteraction.query.filter(
                VocabularyInteraction.student_id == student_id,
                VocabularyInteraction.word == interaction.word,
                VocabularyInteraction.reading_session_id != reading_session_id
            ).count()

            if previous_lookups > 0:
                repeated_lookups.append({
                    **word_data,
                    "previous_lookups": previous_lookups
                })

        # Gather comprehension mistakes
        responses = ReadingResponse.query.filter_by(
            reading_session_id=reading_session_id
        ).all()

        incorrect_questions = []
        correct_questions = []
        question_types_struggled = []

        for response in responses:
            question_data = {
                "question_id": response.question_id,
                "student_answer": response.student_answer,
                "is_correct": response.is_correct,
                "time_spent": response.time_spent
            }

            if response.is_correct:
                correct_questions.append(question_data)
            else:
                incorrect_questions.append(question_data)
                # In a real system, we'd extract question type from ComprehensionQuestion table
                # For now, we'll infer based on patterns
                question_types_struggled.append("inference")  # Placeholder

        # === NEW: Gather chatbot interactions ===
        from app.models.reading import ChatbotInteraction

        chatbot_interactions = ChatbotInteraction.query.filter_by(
            student_id=student_id,
            reading_session_id=reading_session_id
        ).all()

        chatbot_questions_asked = []
        chatbot_topics_confused = []
        chatbot_repeated_topics = []

        topic_counts = {}  # Track topic frequency

        for interaction in chatbot_interactions:
            # Store what they asked
            chatbot_questions_asked.append({
                "question": interaction.user_message[:100],  # First 100 chars
                "type": interaction.message_type,
                "topic": interaction.topic_category
            })

            # Track topics they needed help with
            if interaction.topic_category:
                topic = interaction.topic_category
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
                chatbot_topics_confused.append(topic)

            # Check if this is a repeated topic
            if interaction.is_repeated_topic:
                chatbot_repeated_topics.append({
                    "topic": interaction.topic_category,
                    "question": interaction.user_message[:100]
                })

        # Deduplicate topics
        chatbot_topics_confused = list(set(chatbot_topics_confused))

        # Identify chronic confusion (asked about 2+ times)
        chronic_topics = [topic for topic, count in topic_counts.items() if count >= 2]

        # Analyze reading patterns
        reading_speed_issue = False
        if session.words_per_minute and session.words_per_minute < 100:
            reading_speed_issue = True  # Too slow for advanced learner

        completion_rate = session.reading_completion_percentage or 0

        # Determine engagement level
        engagement_level = "high"
        if session.vocabulary_clicks < 3:
            engagement_level = "low"
        elif session.vocabulary_clicks < 10:
            engagement_level = "medium"

        # Create insight object (but don't generate AI summary yet)
        insight = ReadingMemoryInsight(
            student_id=student_id,
            reading_session_id=reading_session_id,
            vocabulary_mistakes=vocabulary_mistakes,
            difficult_words=difficult_words,
            repeated_lookups=repeated_lookups,
            incorrect_questions=incorrect_questions,
            correct_questions=correct_questions,
            question_types_struggled=list(set(question_types_struggled)),  # Unique types
            chatbot_questions_asked=chatbot_questions_asked,  # NEW
            chatbot_topics_confused=chatbot_topics_confused,  # NEW
            chatbot_repeated_topics=chatbot_repeated_topics,  # NEW
            reading_speed_issue=reading_speed_issue,
            completion_rate=completion_rate,
            engagement_level=engagement_level,
            text_category=session.text_category,
            text_difficulty=session.text_difficulty_level,
            text_topic=session.text_title,
            ai_summary=None,  # Will be generated during compression
            key_issues=[]  # Will be extracted during compression
        )

        db.session.add(insight)
        db.session.commit()

        logger.info(f"Extracted reading insights for session {reading_session_id}")

        # Increment counter on memory board
        memory_board = self.get_or_create_memory_board(student_id)
        memory_board.reading_sessions_since_compression += 1
        db.session.commit()

        return insight

    def compress_reading_memory(self, student_id: int, use_ai: bool = True) -> Dict:
        """
        Compress all uncompressed reading insights into the memory board.

        This function:
        1. Gathers all uncompressed ReadingMemoryInsight records
        2. Uses GPT-4 to extract patterns and key issues
        3. Updates the StudentMemoryBoard with compressed summary
        4. Marks insights as compressed

        Args:
            student_id: Student to compress memory for
            use_ai: If True, use GPT-4 for intelligent compression. If False, use rule-based.

        Returns:
            Compressed memory dict
        """
        # Get all uncompressed insights
        insights = ReadingMemoryInsight.query.filter_by(
            student_id=student_id,
            is_compressed=False
        ).order_by(ReadingMemoryInsight.created_at.desc()).all()

        if not insights:
            logger.info(f"No uncompressed reading insights for student {student_id}")
            return {}

        # Aggregate data from all insights
        all_vocabulary_mistakes = []
        all_difficult_words = []
        all_repeated_lookups = []
        all_incorrect_questions = []
        all_question_types = []
        speed_issues_count = 0
        low_completion_count = 0

        for insight in insights:
            all_vocabulary_mistakes.extend(insight.vocabulary_mistakes or [])
            all_difficult_words.extend(insight.difficult_words or [])
            all_repeated_lookups.extend(insight.repeated_lookups or [])
            all_incorrect_questions.extend(insight.incorrect_questions or [])
            all_question_types.extend(insight.question_types_struggled or [])

            if insight.reading_speed_issue:
                speed_issues_count += 1
            if insight.completion_rate < 80:
                low_completion_count += 1

        # Find most problematic words (appeared multiple times)
        word_frequency = {}
        for word_data in all_vocabulary_mistakes:
            word = word_data.get('word', '')
            if word:
                word_frequency[word] = word_frequency.get(word, 0) + 1

        chronic_vocabulary_gaps = [
            {"word": word, "frequency": count, "priority": "high" if count >= 3 else "medium"}
            for word, count in word_frequency.items()
            if count >= 2
        ]

        # Find most problematic question types
        question_type_frequency = {}
        for qtype in all_question_types:
            question_type_frequency[qtype] = question_type_frequency.get(qtype, 0) + 1

        comprehension_weaknesses = [
            {"skill": qtype, "frequency": count, "priority": "high" if count >= 3 else "medium"}
            for qtype, count in question_type_frequency.items()
        ]

        # Build compressed memory structure
        compressed_memory = {
            "vocabulary_gaps": chronic_vocabulary_gaps[:10],  # Top 10 problem words
            "comprehension_weaknesses": comprehension_weaknesses,
            "reading_speed_issue": speed_issues_count > len(insights) / 2,  # More than half sessions
            "completion_issue": low_completion_count > len(insights) / 2,
            "total_sessions_analyzed": len(insights),
            "last_compressed_at": datetime.utcnow().isoformat(),
            "summary": None  # Will be filled by AI if use_ai=True
        }

        # Use AI to generate human-readable summary (optional)
        if use_ai:
            try:
                from app.api.openai_client import OpenAIClient
                openai_client = OpenAIClient()

                # Prepare data for GPT
                insights_summary = {
                    "total_sessions": len(insights),
                    "vocabulary_issues": chronic_vocabulary_gaps[:5],
                    "comprehension_issues": comprehension_weaknesses,
                    "speed_issue": compressed_memory["reading_speed_issue"],
                    "completion_issue": compressed_memory["completion_issue"]
                }

                prompt = f"""
                You are analyzing a student's reading performance across {len(insights)} sessions.

                Data summary:
                {json.dumps(insights_summary, indent=2)}

                Provide a brief (2-3 sentences) summary of the student's main challenges in reading.
                Focus on actionable patterns. Be specific and encouraging but honest.

                Format: "The student consistently struggles with [pattern]. They show difficulty with [specific issue]. Recommend focusing on [area]."
                """

                ai_response = openai_client.generate_content(prompt)
                if isinstance(ai_response, dict) and "content" in ai_response:
                    compressed_memory["summary"] = ai_response["content"].strip()
                else:
                    compressed_memory["summary"] = ai_response.strip() if isinstance(ai_response, str) else "Analysis complete"

                logger.info(f"Generated AI summary for student {student_id} reading memory")

            except Exception as e:
                logger.error(f"Failed to generate AI summary: {str(e)}")
                compressed_memory["summary"] = f"Analyzed {len(insights)} sessions. Focus on vocabulary reinforcement and comprehension practice."

        # Update memory board
        memory_board = self.get_or_create_memory_board(student_id)
        memory_board.reading_memory = compressed_memory
        memory_board.reading_last_compressed_at = datetime.utcnow()
        memory_board.reading_sessions_since_compression = 0

        # Mark all insights as compressed
        for insight in insights:
            insight.is_compressed = True
            insight.compressed_at = datetime.utcnow()

        db.session.commit()

        logger.info(f"Compressed {len(insights)} reading insights for student {student_id}")

        return compressed_memory

    def extract_listening_session_insights(
        self,
        student_id: int,
        session_id: int
    ) -> ListeningMemoryInsight:
        """
        Extract insights from a completed listening session.
        This is called at the END of each listening session.

        Returns a ListeningMemoryInsight object with all the mistakes and patterns.
        """
        from app.models.session import LearningSession

        session = LearningSession.query.get(session_id)
        if not session:
            raise ValueError(f"Listening session {session_id} not found")

        session_data = session.session_data or {}

        # Extract question performance
        detailed_results = session_data.get('detailed_results', [])
        questions = session_data.get('questions', [])

        incorrect_questions = []
        correct_questions = []
        question_types_struggled = []

        for result in detailed_results:
            if result.get('is_correct'):
                correct_questions.append({
                    "question": result.get('question', '')[:100],
                    "answer": result.get('student_answer')
                })
            else:
                incorrect_questions.append({
                    "question": result.get('question', '')[:100],
                    "student_answer": result.get('student_answer'),
                    "correct_answer": result.get('correct_answer')
                })
                # Extract question type (can be enhanced with GPT)
                question_text = result.get('question', '').lower()
                if 'main idea' in question_text or 'primarily about' in question_text:
                    question_types_struggled.append('main_idea')
                elif 'detail' in question_text or 'mentioned' in question_text:
                    question_types_struggled.append('detail')
                elif 'infer' in question_text or 'imply' in question_text or 'suggest' in question_text:
                    question_types_struggled.append('inference')
                else:
                    question_types_struggled.append('general')

        # Audio difficulty analysis
        audio_category = session_data.get('audio_category', 'general')
        audio_difficulty = session_data.get('difficulty', 'intermediate')

        # Determine if audio speed is an issue based on performance
        score = session.performance_score or 0
        audio_speed_issue = score < 50  # If score very low, might be speed issue

        # Create insight object
        insight = ListeningMemoryInsight(
            student_id=student_id,
            session_id=session_id,
            incorrect_questions=incorrect_questions,
            question_types_struggled=list(set(question_types_struggled)),
            correct_questions=correct_questions,
            audio_category=audio_category,
            audio_difficulty=audio_difficulty,
            audio_speed_issue=audio_speed_issue,
            ai_summary=None,  # Will be generated during compression
            key_issues=[]  # Will be extracted during compression
        )

        db.session.add(insight)
        db.session.commit()

        logger.info(f"Extracted listening insights for session {session_id}")

        # Increment counter on memory board
        memory_board = self.get_or_create_memory_board(student_id)
        memory_board.listening_sessions_since_compression += 1
        db.session.commit()

        return insight

    def get_listening_memory(self, student_id: int) -> Dict:
        """
        Get compressed listening memory for a student.
        Returns a dict with question type weaknesses, audio difficulty patterns, etc.
        """
        memory_board = self.get_or_create_memory_board(student_id)
        return memory_board.listening_memory or {}

    def should_compress_listening_memory(self, student_id: int) -> bool:
        """Check if it's time to compress listening insights"""
        memory_board = self.get_or_create_memory_board(student_id)

        uncompressed_count = ListeningMemoryInsight.query.filter_by(
            student_id=student_id,
            is_compressed=False
        ).count()

        return uncompressed_count >= self.COMPRESSION_THRESHOLD

    def compress_listening_memory(self, student_id: int, use_ai: bool = True) -> Dict:
        """
        Compress all uncompressed listening insights into the memory board.
        """
        insights = ListeningMemoryInsight.query.filter_by(
            student_id=student_id,
            is_compressed=False
        ).order_by(ListeningMemoryInsight.created_at.desc()).all()

        if not insights:
            logger.info(f"No uncompressed listening insights for student {student_id}")
            return {}

        # Aggregate data from all insights
        all_incorrect_questions = []
        all_question_types = []
        speed_issues_count = 0

        for insight in insights:
            all_incorrect_questions.extend(insight.incorrect_questions or [])
            all_question_types.extend(insight.question_types_struggled or [])
            if insight.audio_speed_issue:
                speed_issues_count += 1

        # Find most problematic question types
        question_type_frequency = {}
        for qtype in all_question_types:
            question_type_frequency[qtype] = question_type_frequency.get(qtype, 0) + 1

        comprehension_weaknesses = [
            {"skill": qtype, "frequency": count, "priority": "high" if count >= 3 else "medium"}
            for qtype, count in question_type_frequency.items()
        ]

        # Build compressed memory
        compressed_memory = {
            "comprehension_weaknesses": comprehension_weaknesses,
            "audio_speed_issue": speed_issues_count > len(insights) / 2,
            "total_sessions_analyzed": len(insights),
            "last_compressed_at": datetime.utcnow().isoformat(),
            "summary": None
        }

        # Use AI to generate summary
        if use_ai:
            try:
                from app.api.openai_client import OpenAIClient
                openai_client = OpenAIClient()

                insights_summary = {
                    "total_sessions": len(insights),
                    "comprehension_issues": comprehension_weaknesses,
                    "speed_issue": compressed_memory["audio_speed_issue"]
                }

                prompt = f"""
                You are analyzing a student's listening performance across {len(insights)} sessions.

                Data summary:
                {json.dumps(insights_summary, indent=2)}

                Provide a brief (2-3 sentences) summary of the student's main challenges in listening comprehension.
                Focus on actionable patterns. Be specific and encouraging but honest.

                Format: "The student consistently struggles with [pattern]. They show difficulty with [specific issue]. Recommend focusing on [area]."
                """

                ai_response = openai_client.generate_content(prompt)
                if isinstance(ai_response, dict) and "content" in ai_response:
                    compressed_memory["summary"] = ai_response["content"].strip()
                else:
                    compressed_memory["summary"] = ai_response.strip() if isinstance(ai_response, str) else "Analysis complete"

                logger.info(f"Generated AI summary for student {student_id} listening memory")

            except Exception as e:
                logger.error(f"Failed to generate AI summary: {str(e)}")
                compressed_memory["summary"] = f"Analyzed {len(insights)} sessions. Focus on comprehension practice."

        # Update memory board
        memory_board = self.get_or_create_memory_board(student_id)
        memory_board.listening_memory = compressed_memory
        memory_board.listening_last_compressed_at = datetime.utcnow()
        memory_board.listening_sessions_since_compression = 0

        # Mark all insights as compressed
        for insight in insights:
            insight.is_compressed = True
            insight.compressed_at = datetime.utcnow()

        db.session.commit()

        logger.info(f"Compressed {len(insights)} listening insights for student {student_id}")

        return compressed_memory

    def extract_speaking_session_insights(
        self,
        student_id: int,
        speaking_session_id: int
    ) -> SpeakingMemoryInsight:
        """
        Extract insights from a completed speaking session.
        This is called at the END of each speaking practice.

        Returns a SpeakingMemoryInsight object with pronunciation and fluency patterns.
        """
        from app.models.speaking import SpeakingSession

        session = SpeakingSession.query.get(speaking_session_id)
        if not session:
            raise ValueError(f"Speaking session {speaking_session_id} not found")

        # Extract mispronounced words from word_level_analysis
        mispronounced_words = []
        phoneme_errors = []

        word_analysis = session.word_level_analysis or {}
        if isinstance(word_analysis, dict) and 'words' in word_analysis:
            for word_data in word_analysis.get('words', []):
                if isinstance(word_data, dict):
                    accuracy = word_data.get('accuracy_score', 100)
                    if accuracy < 70:  # Low accuracy = mispronounced
                        mispronounced_words.append({
                            "word": word_data.get('word', ''),
                            "accuracy": accuracy,
                            "error_type": word_data.get('error_type', 'unknown')
                        })

                    # Extract phoneme errors
                    phonemes = word_data.get('phonemes', [])
                    if isinstance(phonemes, list):
                        for phoneme in phonemes:
                            if isinstance(phoneme, dict) and phoneme.get('accuracy_score', 100) < 60:
                                phoneme_errors.append({
                                    "phoneme": phoneme.get('phoneme', ''),
                                    "accuracy": phoneme.get('accuracy_score', 0)
                                })

        # Check for past mispronunciations of same words
        chronic_words = []
        for word_data in mispronounced_words:
            word = word_data['word']
            # Check previous sessions
            previous_sessions = SpeakingSession.query.filter(
                SpeakingSession.student_id == student_id,
                SpeakingSession.id != speaking_session_id
            ).all()

            count = 0
            for prev in previous_sessions:
                prev_analysis = prev.word_level_analysis or {}
                if isinstance(prev_analysis, dict) and 'words' in prev_analysis:
                    for prev_word in prev_analysis.get('words', []):
                        if isinstance(prev_word, dict) and prev_word.get('word', '').lower() == word.lower():
                            if prev_word.get('accuracy_score', 100) < 70:
                                count += 1

            if count >= 2:  # Mispronounced 2+ times before
                chronic_words.append({**word_data, "frequency": count})

        # Analyze fluency issues
        fluency_problems = []
        if session.fluency_score and session.fluency_score < 70:
            fluency_problems.append("low_fluency")
        if session.pause_count and session.pause_count > 5:
            fluency_problems.append("excessive_pauses")
        if session.filler_word_count and session.filler_word_count > 3:
            fluency_problems.append("filler_words")

        # Track scores
        accuracy_scores = {
            "pronunciation": session.pronunciation_score or 0,
            "accuracy": session.accuracy_score or 0,
            "fluency": session.fluency_score or 0,
            "completeness": session.completeness_score or 0
        }

        # Create insight object
        insight = SpeakingMemoryInsight(
            student_id=student_id,
            speaking_session_id=speaking_session_id,
            mispronounced_words=mispronounced_words[:20],  # Limit to 20
            phoneme_errors=phoneme_errors[:20],
            fluency_problems=fluency_problems,
            accuracy_scores=accuracy_scores,
            practice_level=session.practice_type,
            ai_summary=None,  # Will be generated during compression
            key_issues=[]  # Will be extracted during compression
        )

        db.session.add(insight)
        db.session.commit()

        logger.info(f"Extracted speaking insights for session {speaking_session_id}")

        # Increment counter on memory board
        memory_board = self.get_or_create_memory_board(student_id)
        memory_board.speaking_sessions_since_compression += 1
        db.session.commit()

        return insight

    def get_speaking_memory(self, student_id: int) -> Dict:
        """
        Get compressed speaking memory for a student.
        Returns a dict with pronunciation patterns, phoneme errors, fluency issues.
        """
        memory_board = self.get_or_create_memory_board(student_id)
        return memory_board.speaking_memory or {}

    def should_compress_speaking_memory(self, student_id: int) -> bool:
        """Check if it's time to compress speaking insights"""
        memory_board = self.get_or_create_memory_board(student_id)

        uncompressed_count = SpeakingMemoryInsight.query.filter_by(
            student_id=student_id,
            is_compressed=False
        ).count()

        return uncompressed_count >= self.COMPRESSION_THRESHOLD

    def compress_speaking_memory(self, student_id: int, use_ai: bool = True) -> Dict:
        """
        Compress all uncompressed speaking insights into the memory board.
        """
        insights = SpeakingMemoryInsight.query.filter_by(
            student_id=student_id,
            is_compressed=False
        ).order_by(SpeakingMemoryInsight.created_at.desc()).all()

        if not insights:
            logger.info(f"No uncompressed speaking insights for student {student_id}")
            return {}

        # Aggregate data from all insights
        all_mispronounced = []
        all_phoneme_errors = []
        all_fluency_issues = []
        chronic_pronunciation_errors = {}

        for insight in insights:
            all_mispronounced.extend(insight.mispronounced_words or [])
            all_phoneme_errors.extend(insight.phoneme_errors or [])
            all_fluency_issues.extend(insight.fluency_problems or [])

        # Find chronic pronunciation problems (words mispronounced multiple times)
        word_frequency = {}
        for word_data in all_mispronounced:
            word = word_data.get('word', '').lower()
            if word:
                if word not in word_frequency:
                    word_frequency[word] = []
                word_frequency[word].append(word_data.get('accuracy', 0))

        chronic_words = [
            {
                "word": word,
                "frequency": len(accuracies),
                "avg_accuracy": sum(accuracies) / len(accuracies),
                "priority": "high" if len(accuracies) >= 3 else "medium"
            }
            for word, accuracies in word_frequency.items()
            if len(accuracies) >= 2
        ]

        # Find problem phonemes
        phoneme_frequency = {}
        for phoneme_data in all_phoneme_errors:
            phoneme = phoneme_data.get('phoneme', '')
            if phoneme:
                if phoneme not in phoneme_frequency:
                    phoneme_frequency[phoneme] = []
                phoneme_frequency[phoneme].append(phoneme_data.get('accuracy', 0))

        problem_phonemes = [
            {
                "phoneme": phoneme,
                "frequency": len(accuracies),
                "avg_accuracy": sum(accuracies) / len(accuracies),
                "priority": "high" if len(accuracies) >= 3 else "medium"
            }
            for phoneme, accuracies in phoneme_frequency.items()
            if len(accuracies) >= 2
        ]

        # Analyze fluency patterns
        fluency_issue_counts = {}
        for issue in all_fluency_issues:
            fluency_issue_counts[issue] = fluency_issue_counts.get(issue, 0) + 1

        fluency_patterns = [
            {"issue": issue, "frequency": count}
            for issue, count in fluency_issue_counts.items()
            if count >= 2
        ]

        # Build compressed memory
        compressed_memory = {
            "chronic_pronunciation_errors": chronic_words[:10],
            "problem_phonemes": problem_phonemes[:10],
            "fluency_patterns": fluency_patterns,
            "total_sessions_analyzed": len(insights),
            "last_compressed_at": datetime.utcnow().isoformat(),
            "summary": None
        }

        # Use AI to generate summary
        if use_ai:
            try:
                from app.api.openai_client import OpenAIClient
                openai_client = OpenAIClient()

                insights_summary = {
                    "total_sessions": len(insights),
                    "chronic_words": chronic_words[:5],
                    "problem_phonemes": problem_phonemes[:5],
                    "fluency_issues": fluency_patterns
                }

                prompt = f"""
                You are analyzing a student's speaking/pronunciation performance across {len(insights)} sessions.

                Data summary:
                {json.dumps(insights_summary, indent=2)}

                Provide a brief (2-3 sentences) summary of the student's main challenges in pronunciation and speaking fluency.
                Focus on actionable patterns. Be specific and encouraging but honest.

                Format: "The student consistently struggles with [pattern]. They show difficulty with [specific sounds]. Recommend focusing on [area]."
                """

                ai_response = openai_client.generate_content(prompt)
                if isinstance(ai_response, dict) and "content" in ai_response:
                    compressed_memory["summary"] = ai_response["content"].strip()
                else:
                    compressed_memory["summary"] = ai_response.strip() if isinstance(ai_response, str) else "Analysis complete"

                logger.info(f"Generated AI summary for student {student_id} speaking memory")

            except Exception as e:
                logger.error(f"Failed to generate AI summary: {str(e)}")
                compressed_memory["summary"] = f"Analyzed {len(insights)} sessions. Focus on pronunciation practice."

        # Update memory board
        memory_board = self.get_or_create_memory_board(student_id)
        memory_board.speaking_memory = compressed_memory
        memory_board.speaking_last_compressed_at = datetime.utcnow()
        memory_board.speaking_sessions_since_compression = 0

        # Mark all insights as compressed
        for insight in insights:
            insight.is_compressed = True
            insight.compressed_at = datetime.utcnow()

        db.session.commit()

        logger.info(f"Compressed {len(insights)} speaking insights for student {student_id}")

        return compressed_memory

    # ============================================================
    # WRITING MODULE MEMORY METHODS
    # ============================================================

    def extract_writing_session_insights(
        self,
        student_id: int,
        session_id: int,
        analysis_data: Dict
    ) -> WritingMemoryInsight:
        """
        Extract insights from a completed writing session.
        This is called at the END of each writing practice after GPT analysis.

        Args:
            student_id: The student ID
            session_id: The LearningSession ID (not a WritingSession)
            analysis_data: The GPT analysis response with grammar, style, content feedback

        Returns a WritingMemoryInsight object with grammar errors, style issues, vocabulary problems.
        """
        from app.models.session import LearningSession

        session = LearningSession.query.get(session_id)
        if not session:
            raise ValueError(f"Learning session {session_id} not found")

        # Extract grammar errors
        grammar_errors = []
        grammar_analysis = analysis_data.get('grammar_analysis', {})
        if grammar_analysis:
            common_errors = grammar_analysis.get('common_errors', [])
            specific_corrections = grammar_analysis.get('specific_corrections', [])

            # Track error types
            for error_type in common_errors:
                if isinstance(error_type, str):
                    grammar_errors.append({
                        "type": error_type,
                        "severity": "medium"
                    })

            # Track specific corrections with types
            for correction in specific_corrections[:10]:  # Limit to 10
                if isinstance(correction, dict):
                    grammar_errors.append({
                        "type": correction.get('type', 'unknown'),
                        "original": correction.get('original', ''),
                        "correction": correction.get('correction', ''),
                        "explanation": correction.get('explanation', ''),
                        "severity": "high"
                    })

        # Extract style issues
        style_issues = []
        style_analysis = analysis_data.get('style_analysis', {})
        if style_analysis:
            suggestions = style_analysis.get('suggestions', [])
            for suggestion in suggestions[:10]:  # Limit to 10
                if isinstance(suggestion, dict):
                    style_issues.append({
                        "issue": suggestion.get('issue', ''),
                        "example": suggestion.get('example', ''),
                        "improvement": suggestion.get('improvement', '')
                    })

        # Extract vocabulary assessment
        vocabulary_issues = []
        vocab_assessment = analysis_data.get('vocabulary_assessment', {})
        if vocab_assessment:
            complexity_level = vocab_assessment.get('complexity_level', 'intermediate')
            suggestions = vocab_assessment.get('suggestions', [])

            if complexity_level == 'basic':
                vocabulary_issues.append({
                    "issue": "limited_vocabulary",
                    "severity": "high"
                })

            for suggestion in suggestions:
                if isinstance(suggestion, str):
                    vocabulary_issues.append({
                        "issue": "vocabulary_suggestion",
                        "suggestion": suggestion
                    })

        # Track sentence-level issues
        sentence_issues = []
        sentence_analysis = analysis_data.get('sentence_by_sentence', [])
        for sent_data in sentence_analysis[:20]:  # Limit to 20
            if isinstance(sent_data, dict):
                analysis = sent_data.get('analysis', {})
                if analysis.get('clarity') in ['Unclear', 'Confusing']:
                    sentence_issues.append({
                        "issue": "unclear_sentence",
                        "sentence": sent_data.get('original', '')[:100]  # Truncate
                    })
                if analysis.get('effectiveness') == 'Weak':
                    sentence_issues.append({
                        "issue": "weak_sentence",
                        "sentence": sent_data.get('original', '')[:100]
                    })

        # Extract content feedback
        content_feedback = analysis_data.get('content_feedback', {})
        weak_content_areas = []
        if content_feedback:
            for area, rating in content_feedback.items():
                if rating in ['weak', 'poor']:
                    weak_content_areas.append({
                        "area": area,
                        "rating": rating
                    })

        # Get overall score
        overall_analysis = analysis_data.get('overall_analysis', {})
        overall_score = overall_analysis.get('score', analysis_data.get('overall_score', 0))
        on_topic = overall_analysis.get('on_topic', True)

        # Determine writing type from session data
        writing_type = session.activity_type or 'general'
        session_data = session.session_data or {}
        topic = session_data.get('topic', 'unknown')

        # Create insight object
        insight = WritingMemoryInsight(
            student_id=student_id,
            learning_session_id=session_id,
            writing_type=writing_type,
            topic=topic,
            grammar_errors=grammar_errors[:20],  # Limit to 20
            style_issues=style_issues[:15],
            vocabulary_issues=vocabulary_issues[:15],
            sentence_issues=sentence_issues[:15],
            content_weaknesses=weak_content_areas,
            overall_score=overall_score,
            on_topic=on_topic,
            ai_summary=None,  # Will be generated during compression
            key_issues=[]  # Will be extracted during compression
        )

        db.session.add(insight)
        db.session.commit()

        logger.info(f"Extracted writing insights for session {session_id}")

        # Increment counter on memory board
        memory_board = self.get_or_create_memory_board(student_id)
        memory_board.writing_sessions_since_compression += 1
        db.session.commit()

        return insight

    def get_writing_memory(self, student_id: int) -> Dict:
        """
        Get compressed writing memory for a student.
        Returns a dict with grammar patterns, style issues, vocabulary weaknesses.
        """
        memory_board = self.get_or_create_memory_board(student_id)
        return memory_board.writing_memory or {}

    def should_compress_writing_memory(self, student_id: int) -> bool:
        """Check if it's time to compress writing insights"""
        memory_board = self.get_or_create_memory_board(student_id)

        uncompressed_count = WritingMemoryInsight.query.filter_by(
            student_id=student_id,
            is_compressed=False
        ).count()

        return uncompressed_count >= self.COMPRESSION_THRESHOLD

    def compress_writing_memory(self, student_id: int, use_ai: bool = True) -> Dict:
        """
        Compress all uncompressed writing insights into the memory board.
        Analyzes grammar patterns, style issues, and vocabulary weaknesses across sessions.
        """
        insights = WritingMemoryInsight.query.filter_by(
            student_id=student_id,
            is_compressed=False
        ).order_by(WritingMemoryInsight.created_at.desc()).all()

        if not insights:
            logger.info(f"No uncompressed writing insights for student {student_id}")
            return {}

        # Aggregate data from all insights
        all_grammar_errors = []
        all_style_issues = []
        all_vocab_issues = []
        all_content_weaknesses = []

        for insight in insights:
            all_grammar_errors.extend(insight.grammar_errors or [])
            all_style_issues.extend(insight.style_issues or [])
            all_vocab_issues.extend(insight.vocabulary_issues or [])
            all_content_weaknesses.extend(insight.content_weaknesses or [])

        # Find chronic grammar errors (error types that repeat)
        grammar_error_frequency = {}
        for error in all_grammar_errors:
            error_type = error.get('type', 'unknown')
            if error_type:
                if error_type not in grammar_error_frequency:
                    grammar_error_frequency[error_type] = []
                grammar_error_frequency[error_type].append(error)

        chronic_grammar_errors = [
            {
                "error_type": error_type,
                "frequency": len(errors),
                "examples": [e.get('original', '') for e in errors[:3] if e.get('original')],
                "priority": "high" if len(errors) >= 3 else "medium"
            }
            for error_type, errors in grammar_error_frequency.items()
            if len(errors) >= 2
        ]

        # Find recurring style issues
        style_issue_frequency = {}
        for issue in all_style_issues:
            issue_type = issue.get('issue', '')
            if issue_type:
                style_issue_frequency[issue_type] = style_issue_frequency.get(issue_type, 0) + 1

        recurring_style_issues = [
            {
                "issue": issue,
                "frequency": count,
                "priority": "high" if count >= 3 else "medium"
            }
            for issue, count in style_issue_frequency.items()
            if count >= 2
        ]

        # Analyze vocabulary patterns
        vocab_issue_frequency = {}
        for issue in all_vocab_issues:
            issue_type = issue.get('issue', '')
            if issue_type:
                vocab_issue_frequency[issue_type] = vocab_issue_frequency.get(issue_type, 0) + 1

        vocabulary_weaknesses = [
            {
                "issue": issue,
                "frequency": count,
                "priority": "high" if count >= 3 else "medium"
            }
            for issue, count in vocab_issue_frequency.items()
            if count >= 2
        ]

        # Analyze content weaknesses
        content_weakness_frequency = {}
        for weakness in all_content_weaknesses:
            area = weakness.get('area', '')
            if area:
                content_weakness_frequency[area] = content_weakness_frequency.get(area, 0) + 1

        content_patterns = [
            {
                "area": area,
                "frequency": count,
                "priority": "high" if count >= 3 else "medium"
            }
            for area, count in content_weakness_frequency.items()
            if count >= 2
        ]

        # Calculate average score trend
        scores = [insight.overall_score for insight in insights if insight.overall_score]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Build compressed memory
        compressed_memory = {
            "chronic_grammar_errors": sorted(chronic_grammar_errors, key=lambda x: x['frequency'], reverse=True)[:10],
            "recurring_style_issues": sorted(recurring_style_issues, key=lambda x: x['frequency'], reverse=True)[:10],
            "vocabulary_weaknesses": vocabulary_weaknesses[:10],
            "content_patterns": content_patterns[:10],
            "average_score": round(avg_score, 1),
            "total_sessions_analyzed": len(insights),
            "last_compressed_at": datetime.utcnow().isoformat(),
            "summary": None
        }

        # Use AI to generate summary
        if use_ai:
            try:
                from app.api.openai_client import OpenAIClient
                openai_client = OpenAIClient()

                insights_summary = {
                    "total_sessions": len(insights),
                    "average_score": avg_score,
                    "chronic_grammar_errors": chronic_grammar_errors[:5],
                    "recurring_style_issues": recurring_style_issues[:5],
                    "vocabulary_weaknesses": vocabulary_weaknesses[:5],
                    "content_patterns": content_patterns[:5]
                }

                prompt = f"""
                You are analyzing a student's writing performance across {len(insights)} sessions.

                Data summary:
                {json.dumps(insights_summary, indent=2)}

                Provide a brief (2-3 sentences) summary of the student's main challenges in writing.
                Focus on actionable patterns. Be specific and encouraging but honest.

                Format: "The student consistently struggles with [grammar pattern]. They show difficulty with [style issue]. Recommend focusing on [specific area]."
                """

                ai_response = openai_client.generate_content(prompt)
                if isinstance(ai_response, dict) and "content" in ai_response:
                    compressed_memory["summary"] = ai_response["content"].strip()
                else:
                    compressed_memory["summary"] = ai_response.strip() if isinstance(ai_response, str) else "Analysis complete"

                logger.info(f"Generated AI summary for student {student_id} writing memory")

            except Exception as e:
                logger.error(f"Failed to generate AI summary: {str(e)}")
                compressed_memory["summary"] = f"Analyzed {len(insights)} sessions. Focus on grammar and style improvement."

        # Update memory board
        memory_board = self.get_or_create_memory_board(student_id)
        memory_board.writing_memory = compressed_memory
        memory_board.writing_last_compressed_at = datetime.utcnow()
        memory_board.writing_sessions_since_compression = 0

        # Mark all insights as compressed
        for insight in insights:
            insight.is_compressed = True
            insight.compressed_at = datetime.utcnow()

        db.session.commit()

        logger.info(f"Compressed {len(insights)} writing insights for student {student_id}")

        return compressed_memory

    # ============================================================
    # CONVERSATION MODULE MEMORY METHODS
    # ============================================================

    def extract_conversation_session_insights(
        self,
        student_id: int,
        session_data: Dict
    ) -> ConversationMemoryInsight:
        """
        Extract insights from a completed conversation session.
        This is called at the END of each conversation with the Avatar.

        Args:
            student_id: The student ID
            session_data: Dictionary with conversation messages and analytics

        Returns a ConversationMemoryInsight object with grammar errors, vocabulary gaps, topic struggles.
        """
        messages = session_data.get('messages', [])
        analytics = session_data.get('analytics', {})
        topic = session_data.get('topic', 'general_conversation')

        # Extract student messages only
        student_messages = [msg for msg in messages if msg.get('role') == 'user']

        # Use GPT to analyze conversation for errors
        grammar_errors = []
        vocabulary_gaps = []
        fluency_issues = []
        topic_struggles = []
        mispronounced_words = []
        phoneme_errors = []
        pronunciation_scores = {}

        # Extract pronunciation data if available (from audio conversations)
        pronunciation_data = session_data.get('pronunciation_data', {})
        if pronunciation_data:
            mispronounced_words = pronunciation_data.get('mispronounced_words', [])
            phoneme_errors = pronunciation_data.get('phoneme_errors', [])
            pronunciation_scores = pronunciation_data.get('scores', {})

        if len(student_messages) >= 3:  # Only analyze if enough messages
            try:
                from app.api.openai_client import OpenAIClient
                openai_client = OpenAIClient()

                # Build conversation transcript
                student_turns = "\n".join([
                    f"Student: {msg.get('content', '')}"
                    for msg in student_messages[:10]  # Analyze up to 10 messages
                ])

                analysis_prompt = f"""
                Analyze this student's conversation in English and identify errors and weak areas.

                Topic: {topic}
                Student's messages:
                {student_turns}

                Return ONLY valid JSON with this structure:
                {{
                    "grammar_errors": [
                        {{"type": "error_type", "example": "original text", "correction": "corrected version"}}
                    ],
                    "vocabulary_gaps": [
                        {{"word": "word they struggled with", "context": "how it was used", "issue": "description"}}
                    ],
                    "fluency_issues": ["list", "of", "fluency", "problems"],
                    "topic_struggles": ["topics", "they", "struggled", "with"],
                    "question_formation_errors": ["examples", "of", "incorrect", "questions"]
                }}

                Focus on actual errors you observe. If none, return empty arrays.
                """

                ai_response = openai_client.generate_content(
                    analysis_prompt,
                    max_tokens=800,
                    temperature=0.3
                )

                # Parse GPT response
                if isinstance(ai_response, dict) and 'content' in ai_response:
                    analysis_data = json.loads(ai_response['content'])
                elif isinstance(ai_response, str):
                    analysis_data = json.loads(ai_response)
                else:
                    analysis_data = {}

                grammar_errors = analysis_data.get('grammar_errors', [])[:15]
                vocabulary_gaps = analysis_data.get('vocabulary_gaps', [])[:15]
                fluency_issues = analysis_data.get('fluency_issues', [])
                topic_struggles = analysis_data.get('topic_struggles', [])

            except Exception as e:
                logger.error(f"Failed to analyze conversation with GPT: {str(e)}")
                # Fallback: basic pattern matching
                all_text = " ".join([msg.get('content', '') for msg in student_messages])
                if len(all_text.split()) < 50:
                    fluency_issues.append("short_responses")

        # Get basic metrics from analytics
        total_words = analytics.get('total_words_spoken', 0)
        total_messages = analytics.get('total_exchanges', 0)
        avg_words_per_message = analytics.get('average_words_per_message', 0)

        if avg_words_per_message < 5:
            fluency_issues.append("very_short_responses")

        # Create insight object
        insight = ConversationMemoryInsight(
            student_id=student_id,
            topic=topic,
            grammar_errors=grammar_errors,
            vocabulary_gaps=vocabulary_gaps,
            fluency_issues=fluency_issues,
            topic_struggles=topic_struggles,
            mispronounced_words=mispronounced_words,
            phoneme_errors=phoneme_errors,
            pronunciation_scores=pronunciation_scores,
            total_messages=total_messages,
            total_words=total_words,
            avg_words_per_message=avg_words_per_message,
            ai_summary=None,  # Will be generated during compression
            key_issues=[]  # Will be extracted during compression
        )

        db.session.add(insight)
        db.session.commit()

        logger.info(f"Extracted conversation insights for student {student_id}")

        # Increment counter on memory board
        memory_board = self.get_or_create_memory_board(student_id)
        memory_board.conversation_sessions_since_compression += 1
        db.session.commit()

        return insight

    def get_conversation_memory(self, student_id: int) -> Dict:
        """
        Get compressed conversation memory for a student.
        Returns a dict with grammar patterns, vocabulary gaps, topic struggles.
        """
        memory_board = self.get_or_create_memory_board(student_id)
        return memory_board.conversation_memory or {}

    def should_compress_conversation_memory(self, student_id: int) -> bool:
        """Check if it's time to compress conversation insights"""
        memory_board = self.get_or_create_memory_board(student_id)

        uncompressed_count = ConversationMemoryInsight.query.filter_by(
            student_id=student_id,
            is_compressed=False
        ).count()

        return uncompressed_count >= self.COMPRESSION_THRESHOLD

    def compress_conversation_memory(self, student_id: int, use_ai: bool = True) -> Dict:
        """
        Compress all uncompressed conversation insights into the memory board.
        Analyzes grammar patterns, vocabulary gaps, and topic weaknesses across sessions.
        """
        insights = ConversationMemoryInsight.query.filter_by(
            student_id=student_id,
            is_compressed=False
        ).order_by(ConversationMemoryInsight.created_at.desc()).all()

        if not insights:
            logger.info(f"No uncompressed conversation insights for student {student_id}")
            return {}

        # Aggregate data from all insights
        all_grammar_errors = []
        all_vocab_gaps = []
        all_fluency_issues = []
        all_topic_struggles = []
        all_mispronounced_words = []
        all_phoneme_errors = []

        for insight in insights:
            all_grammar_errors.extend(insight.grammar_errors or [])
            all_vocab_gaps.extend(insight.vocabulary_gaps or [])
            all_fluency_issues.extend(insight.fluency_issues or [])
            all_topic_struggles.extend(insight.topic_struggles or [])
            all_mispronounced_words.extend(insight.mispronounced_words or [])
            all_phoneme_errors.extend(insight.phoneme_errors or [])

        # Find chronic grammar errors (error types that repeat)
        grammar_error_frequency = {}
        for error in all_grammar_errors:
            if isinstance(error, dict):
                error_type = error.get('type', 'unknown')
                if error_type:
                    if error_type not in grammar_error_frequency:
                        grammar_error_frequency[error_type] = []
                    grammar_error_frequency[error_type].append(error)

        chronic_grammar_errors = [
            {
                "error_type": error_type,
                "frequency": len(errors),
                "examples": [e.get('example', '') for e in errors[:3] if e.get('example')],
                "corrections": [e.get('correction', '') for e in errors[:3] if e.get('correction')],
                "priority": "high" if len(errors) >= 3 else "medium"
            }
            for error_type, errors in grammar_error_frequency.items()
            if len(errors) >= 2
        ]

        # Find recurring vocabulary gaps
        vocab_gap_frequency = {}
        for gap in all_vocab_gaps:
            if isinstance(gap, dict):
                word = gap.get('word', '')
                if word:
                    if word not in vocab_gap_frequency:
                        vocab_gap_frequency[word] = []
                    vocab_gap_frequency[word].append(gap)

        chronic_vocab_gaps = [
            {
                "word": word,
                "frequency": len(gaps),
                "contexts": [g.get('context', '') for g in gaps[:2] if g.get('context')],
                "priority": "high" if len(gaps) >= 2 else "medium"
            }
            for word, gaps in vocab_gap_frequency.items()
            if len(gaps) >= 1
        ]

        # Analyze fluency patterns
        fluency_issue_frequency = {}
        for issue in all_fluency_issues:
            if isinstance(issue, str):
                fluency_issue_frequency[issue] = fluency_issue_frequency.get(issue, 0) + 1

        fluency_patterns = [
            {
                "issue": issue,
                "frequency": count,
                "priority": "high" if count >= 3 else "medium"
            }
            for issue, count in fluency_issue_frequency.items()
            if count >= 2
        ]

        # Analyze topic struggles
        topic_struggle_frequency = {}
        for topic in all_topic_struggles:
            if isinstance(topic, str):
                topic_struggle_frequency[topic] = topic_struggle_frequency.get(topic, 0) + 1

        topic_patterns = [
            {
                "topic": topic,
                "frequency": count,
                "priority": "high" if count >= 2 else "medium"
            }
            for topic, count in topic_struggle_frequency.items()
            if count >= 1
        ]

        # Analyze pronunciation patterns (similar to Speaking module)
        word_pronunciation_frequency = {}
        for word_data in all_mispronounced_words:
            if isinstance(word_data, dict):
                word = word_data.get('word', '').lower()
                if word:
                    if word not in word_pronunciation_frequency:
                        word_pronunciation_frequency[word] = []
                    word_pronunciation_frequency[word].append(word_data.get('accuracy', 0))

        chronic_mispronunciations = [
            {
                "word": word,
                "frequency": len(accuracies),
                "avg_accuracy": sum(accuracies) / len(accuracies) if accuracies else 0,
                "priority": "high" if len(accuracies) >= 2 else "medium"
            }
            for word, accuracies in word_pronunciation_frequency.items()
            if len(accuracies) >= 1
        ]

        # Analyze phoneme errors
        phoneme_frequency = {}
        for phoneme_data in all_phoneme_errors:
            if isinstance(phoneme_data, dict):
                phoneme = phoneme_data.get('phoneme', '')
                if phoneme:
                    if phoneme not in phoneme_frequency:
                        phoneme_frequency[phoneme] = []
                    phoneme_frequency[phoneme].append(phoneme_data.get('accuracy', 0))

        problem_phonemes = [
            {
                "phoneme": phoneme,
                "frequency": len(accuracies),
                "avg_accuracy": sum(accuracies) / len(accuracies) if accuracies else 0,
                "priority": "high" if len(accuracies) >= 2 else "medium"
            }
            for phoneme, accuracies in phoneme_frequency.items()
            if len(accuracies) >= 1
        ]

        # Calculate average metrics
        total_words = sum(insight.total_words or 0 for insight in insights)
        total_messages = sum(insight.total_messages or 0 for insight in insights)
        avg_words_per_session = total_words / len(insights) if insights else 0

        # Build compressed memory
        compressed_memory = {
            "chronic_grammar_errors": sorted(chronic_grammar_errors, key=lambda x: x['frequency'], reverse=True)[:10],
            "vocabulary_gaps": sorted(chronic_vocab_gaps, key=lambda x: x['frequency'], reverse=True)[:10],
            "fluency_patterns": fluency_patterns[:10],
            "topic_struggles": topic_patterns[:10],
            "chronic_mispronunciations": sorted(chronic_mispronunciations, key=lambda x: x['frequency'], reverse=True)[:10],
            "problem_phonemes": sorted(problem_phonemes, key=lambda x: x['frequency'], reverse=True)[:10],
            "avg_words_per_session": round(avg_words_per_session, 1),
            "total_sessions_analyzed": len(insights),
            "last_compressed_at": datetime.utcnow().isoformat(),
            "summary": None
        }

        # Use AI to generate summary
        if use_ai:
            try:
                from app.api.openai_client import OpenAIClient
                openai_client = OpenAIClient()

                insights_summary = {
                    "total_sessions": len(insights),
                    "avg_words_per_session": avg_words_per_session,
                    "chronic_grammar_errors": chronic_grammar_errors[:5],
                    "vocabulary_gaps": chronic_vocab_gaps[:5],
                    "fluency_patterns": fluency_patterns[:5],
                    "topic_struggles": topic_patterns[:5],
                    "chronic_mispronunciations": chronic_mispronunciations[:5],
                    "problem_phonemes": problem_phonemes[:5]
                }

                prompt = f"""
                You are analyzing a student's conversational English performance across {len(insights)} sessions.

                Data summary:
                {json.dumps(insights_summary, indent=2)}

                Provide a brief (2-3 sentences) summary of the student's main challenges in conversational English.
                Focus on actionable patterns. Be specific and encouraging but honest.
                Include pronunciation issues if present.

                Format: "The student consistently struggles with [grammar pattern]. They show difficulty with [vocabulary/fluency/pronunciation issue]. Recommend focusing on [specific area]."
                """

                ai_response = openai_client.generate_content(prompt)
                if isinstance(ai_response, dict) and "content" in ai_response:
                    compressed_memory["summary"] = ai_response["content"].strip()
                else:
                    compressed_memory["summary"] = ai_response.strip() if isinstance(ai_response, str) else "Analysis complete"

                logger.info(f"Generated AI summary for student {student_id} conversation memory")

            except Exception as e:
                logger.error(f"Failed to generate AI summary: {str(e)}")
                compressed_memory["summary"] = f"Analyzed {len(insights)} sessions. Focus on grammar and fluency improvement."

        # Update memory board
        memory_board = self.get_or_create_memory_board(student_id)
        memory_board.conversation_memory = compressed_memory
        memory_board.conversation_last_compressed_at = datetime.utcnow()
        memory_board.conversation_sessions_since_compression = 0

        # Mark all insights as compressed
        for insight in insights:
            insight.is_compressed = True
            insight.compressed_at = datetime.utcnow()

        db.session.commit()

        logger.info(f"Compressed {len(insights)} conversation insights for student {student_id}")

        return compressed_memory

    def get_adaptive_question_focus(self, student_id: int) -> Dict:
        """
        Get question generation hints based on student's memory.

        This is used by the reading question generation to adapt questions
        to focus on the student's weak areas.

        Returns dict with:
        - focus_topics: Topics to emphasize in questions
        - avoid_words: Words student knows well (don't test again)
        - challenge_words: Words to include in questions
        - question_types_priority: Which types of questions to generate more of
        """
        memory = self.get_reading_memory(student_id)

        if not memory:
            return {
                "focus_topics": [],
                "challenge_words": [],
                "question_types_priority": ["inference", "main_idea", "detail", "vocabulary"],
                "difficulty_level": "intermediate"
            }

        # Extract vocabulary to challenge
        challenge_words = [
            item["word"]
            for item in memory.get("vocabulary_gaps", [])
            if item.get("priority") in ["high", "medium"]
        ][:5]  # Top 5

        # Determine which question types to prioritize
        weak_areas = memory.get("comprehension_weaknesses", [])
        question_types_priority = [item["skill"] for item in weak_areas if item.get("priority") == "high"]

        # Add standard types if no weak areas identified
        if not question_types_priority:
            question_types_priority = ["inference", "main_idea", "detail"]

        return {
            "focus_topics": [],  # Could be expanded later
            "challenge_words": challenge_words,
            "question_types_priority": question_types_priority,
            "difficulty_level": "advanced" if len(memory.get("vocabulary_gaps", [])) < 3 else "intermediate",
            "memory_summary": memory.get("summary", "")
        }


# Singleton instance
_memory_service_instance = None

def get_memory_service() -> MemoryService:
    """Get singleton instance of MemoryService"""
    global _memory_service_instance
    if _memory_service_instance is None:
        _memory_service_instance = MemoryService()
    return _memory_service_instance
