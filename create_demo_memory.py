#!/usr/bin/env python3
"""
Create Demo Memory Board Data

This script creates realistic demo memory data for a student across all modules.
This data will be shown during avatar conversations to demonstrate the memory feature.

Usage:
    python create_demo_memory.py
"""

import os
import sys
from datetime import datetime, timedelta
from app import create_app, db
from app.models.memory import StudentMemoryBoard
from app.models.user import Student
from config import config

def create_demo_memory():
    """Create comprehensive demo memory data for student"""

    # Get app with appropriate config
    env = os.environ.get('FLASK_ENV', 'development')
    app = create_app(config[env])

    with app.app_context():
        print("=" * 60)
        print("CREATING DEMO MEMORY BOARD DATA")
        print("=" * 60)

        # Get or create demo student (usually ID 1)
        student = Student.query.filter_by(username='demo_student').first()
        if not student:
            # Try to get first student
            student = Student.query.first()
            if not student:
                print("❌ No student found! Please create a student first.")
                sys.exit(1)

        print(f"\n📊 Creating memory data for: {student.username} (ID: {student.id})")

        # Check if memory board already exists
        memory_board = StudentMemoryBoard.query.filter_by(student_id=student.id).first()

        if memory_board:
            print("⚠️  Memory board already exists. Updating with demo data...")
        else:
            print("✨ Creating new memory board...")
            memory_board = StudentMemoryBoard(student_id=student.id)
            db.session.add(memory_board)

        # === READING MODULE MEMORY ===
        print("\n📚 Adding Reading module memory...")
        memory_board.reading_memory = {
            "vocabulary_gaps": [
                {"word": "ephemeral", "frequency": 3, "priority": "high"},
                {"word": "ubiquitous", "frequency": 2, "priority": "medium"},
                {"word": "pragmatic", "frequency": 2, "priority": "medium"}
            ],
            "comprehension_weaknesses": [
                {"skill": "inference", "frequency": 4, "priority": "high"},
                {"skill": "main_idea", "frequency": 2, "priority": "medium"}
            ],
            "chatbot_topics_confused": [
                {"topic": "metaphor_interpretation", "frequency": 2},
                {"topic": "passive_voice_understanding", "frequency": 1}
            ],
            "reading_speed_issue": False,
            "completion_issue": False,
            "total_sessions_analyzed": 5,
            "last_compressed_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "summary": "Student struggles with inference questions and abstract vocabulary like 'ephemeral' and 'ubiquitous'. They tend to focus on literal meaning and miss implied context. Reading comprehension is good for direct questions but weak for interpretive analysis."
        }
        memory_board.reading_last_compressed_at = datetime.utcnow() - timedelta(days=1)

        # === LISTENING MODULE MEMORY ===
        print("🎧 Adding Listening module memory...")
        memory_board.listening_memory = {
            "comprehension_weaknesses": [
                {"skill": "detail", "frequency": 3, "priority": "high"},
                {"skill": "inference", "frequency": 2, "priority": "medium"}
            ],
            "audio_speed_issue": True,
            "total_sessions_analyzed": 4,
            "last_compressed_at": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "summary": "Student struggles with fast-paced audio content and detail-oriented questions. They often miss specific numbers, dates, and factual details when listening at normal speed. Inference from context is also challenging. Recommend slowing down audio practice and focusing on note-taking skills."
        }
        memory_board.listening_last_compressed_at = datetime.utcnow() - timedelta(days=2)

        # === SPEAKING MODULE MEMORY ===
        print("🗣️ Adding Speaking module memory...")
        memory_board.speaking_memory = {
            "chronic_mispronunciations": [
                {"word": "th", "frequency": 5, "avg_accuracy": 65, "priority": "high"},
                {"word": "comfortable", "frequency": 3, "avg_accuracy": 70, "priority": "high"},
                {"word": "world", "frequency": 2, "avg_accuracy": 75, "priority": "medium"}
            ],
            "problem_phonemes": [
                {"phoneme": "θ", "frequency": 6, "avg_accuracy": 60, "priority": "high"},
                {"phoneme": "ð", "frequency": 5, "avg_accuracy": 62, "priority": "high"},
                {"phoneme": "r", "frequency": 3, "avg_accuracy": 72, "priority": "medium"}
            ],
            "fluency_patterns": [
                {"issue": "excessive_pauses", "frequency": 4},
                {"issue": "filler_words", "frequency": 3}
            ],
            "total_sessions_analyzed": 6,
            "last_compressed_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "summary": "Student consistently struggles with 'th' sounds (θ, ð), pronouncing them as 't' or 'd'. Words like 'comfortable' and 'world' are also problematic. Fluency is affected by excessive pauses and filler words ('um', 'uh'). Recommend focused phonetic practice on dental fricatives and breathing exercises for smoother speech flow."
        }
        memory_board.speaking_last_compressed_at = datetime.utcnow() - timedelta(days=1)

        # === WRITING MODULE MEMORY ===
        print("✍️ Adding Writing module memory...")
        memory_board.writing_memory = {
            "chronic_grammar_errors": [
                {
                    "error_type": "article_usage",
                    "frequency": 5,
                    "examples": ["I went to school", "The knowledge is power"],
                    "priority": "high"
                },
                {
                    "error_type": "preposition_errors",
                    "frequency": 4,
                    "examples": ["depend of", "interested on"],
                    "priority": "high"
                },
                {
                    "error_type": "subject_verb_agreement",
                    "frequency": 3,
                    "examples": ["She don't like", "The students was"],
                    "priority": "medium"
                }
            ],
            "recurring_style_issues": [
                {"issue": "run_on_sentences", "frequency": 4, "priority": "high"},
                {"issue": "repetitive_vocabulary", "frequency": 3, "priority": "medium"},
                {"issue": "informal_tone", "frequency": 2, "priority": "medium"}
            ],
            "vocabulary_issues": [
                {"word": "limited_vocabulary", "frequency": 3, "priority": "high"}
            ],
            "content_patterns": [
                {"area": "logical_flow", "frequency": 3, "priority": "high"},
                {"area": "supporting_evidence", "frequency": 2, "priority": "medium"}
            ],
            "average_score": 72.5,
            "total_sessions_analyzed": 4,
            "last_compressed_at": (datetime.utcnow() - timedelta(days=3)).isoformat(),
            "summary": "Student consistently struggles with article usage (a/an/the) and preposition selection. Run-on sentences are common, affecting clarity. Vocabulary is somewhat limited and repetitive. Recommend focusing on article rules, preposition collocations, and sentence structure practice. Content organization needs work with logical transitions."
        }
        memory_board.writing_last_compressed_at = datetime.utcnow() - timedelta(days=3)

        # === CONVERSATION MODULE MEMORY ===
        print("💬 Adding Conversation module memory...")
        memory_board.conversation_memory = {
            "chronic_grammar_errors": [
                {
                    "error_type": "present_perfect_usage",
                    "frequency": 3,
                    "examples": ["I already ate", "Did you ever been to"],
                    "corrections": ["I have already eaten", "Have you ever been to"],
                    "priority": "high"
                },
                {
                    "error_type": "question_formation",
                    "frequency": 2,
                    "examples": ["Why you did that?", "Where he went?"],
                    "corrections": ["Why did you do that?", "Where did he go?"],
                    "priority": "medium"
                }
            ],
            "vocabulary_gaps": [
                {"word": "colleagues", "frequency": 2, "contexts": ["work environment", "team discussion"], "priority": "high"},
                {"word": "maintain", "frequency": 1, "contexts": ["relationship discussion"], "priority": "medium"}
            ],
            "fluency_patterns": [
                {"issue": "short_responses", "frequency": 3, "priority": "medium"},
                {"issue": "very_short_responses", "frequency": 2, "priority": "high"}
            ],
            "topic_struggles": [
                {"topic": "abstract_concepts", "frequency": 2, "priority": "high"},
                {"topic": "business_vocabulary", "frequency": 1, "priority": "medium"}
            ],
            "chronic_mispronunciations": [
                {"word": "th", "frequency": 4, "avg_accuracy": 65, "priority": "high"},
                {"word": "comfortable", "frequency": 2, "avg_accuracy": 70, "priority": "medium"}
            ],
            "problem_phonemes": [
                {"phoneme": "θ", "frequency": 5, "avg_accuracy": 62, "priority": "high"},
                {"phoneme": "ð", "frequency": 4, "avg_accuracy": 63, "priority": "high"}
            ],
            "avg_words_per_session": 145.5,
            "total_sessions_analyzed": 3,
            "last_compressed_at": (datetime.utcnow() - timedelta(hours=12)).isoformat(),
            "summary": "Student shows difficulty with present perfect tense and question word order. Responses tend to be brief (averaging 145 words/session), limiting conversational depth. Pronunciation of 'th' sounds remains challenging. Abstract topics and business vocabulary cause hesitation. Recommend more elaboration practice, present perfect drills, and exposure to abstract discussion topics."
        }
        memory_board.conversation_last_compressed_at = datetime.utcnow() - timedelta(hours=12)

        # === OVERALL PATTERNS ===
        print("🎯 Adding cross-module patterns...")
        memory_board.overall_patterns = {
            "cross_module_issues": [
                {
                    "issue": "th_pronunciation",
                    "modules": ["speaking", "conversation"],
                    "priority": "critical",
                    "description": "Consistent difficulty with dental fricatives (θ, ð) across all speaking activities"
                },
                {
                    "issue": "abstract_vocabulary",
                    "modules": ["reading", "conversation", "writing"],
                    "priority": "high",
                    "description": "Struggles with abstract/academic vocabulary and concepts across multiple modules"
                },
                {
                    "issue": "inference_skills",
                    "modules": ["reading", "listening"],
                    "priority": "high",
                    "description": "Difficulty inferring meaning from context in both reading and listening"
                },
                {
                    "issue": "grammar_consistency",
                    "modules": ["writing", "conversation"],
                    "priority": "high",
                    "description": "Article usage and tense errors appear in both written and spoken English"
                }
            ],
            "strengths": [
                "Strong engagement and completion rates in all modules",
                "Good reading speed and general comprehension of direct questions",
                "Consistent practice across all learning areas"
            ],
            "recommended_focus_areas": [
                "Pronunciation: Intensive 'th' sound practice with minimal pairs",
                "Grammar: Article usage (a/an/the) and present perfect tense",
                "Vocabulary: Abstract and academic vocabulary building",
                "Skills: Inference practice in reading and listening contexts",
                "Fluency: Elaboration and extended response practice"
            ]
        }

        # Update timestamp
        memory_board.updated_at = datetime.utcnow()

        # Commit to database
        try:
            db.session.commit()
            print("\n✅ Demo memory data created successfully!")

            # Print summary
            print("\n" + "=" * 60)
            print("DEMO MEMORY BOARD SUMMARY")
            print("=" * 60)
            print(f"\n👤 Student: {student.username} (ID: {student.id})")
            print(f"\n📚 Reading Memory:")
            print(f"   • Vocabulary gaps: {len(memory_board.reading_memory['vocabulary_gaps'])} words")
            print(f"   • Comprehension weaknesses: {len(memory_board.reading_memory['comprehension_weaknesses'])} areas")
            print(f"\n🎧 Listening Memory:")
            print(f"   • Comprehension weaknesses: {len(memory_board.listening_memory['comprehension_weaknesses'])} areas")
            print(f"   • Audio speed issue: Yes")
            print(f"\n🗣️ Speaking Memory:")
            print(f"   • Pronunciation errors: {len(memory_board.speaking_memory['chronic_mispronunciations'])} words")
            print(f"   • Problem phonemes: {len(memory_board.speaking_memory['problem_phonemes'])} sounds")
            print(f"\n✍️ Writing Memory:")
            print(f"   • Grammar errors: {len(memory_board.writing_memory['chronic_grammar_errors'])} patterns")
            print(f"   • Style issues: {len(memory_board.writing_memory['recurring_style_issues'])} areas")
            print(f"   • Average score: {memory_board.writing_memory['average_score']}/100")
            print(f"\n💬 Conversation Memory:")
            print(f"   • Grammar errors: {len(memory_board.conversation_memory['chronic_grammar_errors'])} patterns")
            print(f"   • Vocabulary gaps: {len(memory_board.conversation_memory['vocabulary_gaps'])} words")
            print(f"   • Topic struggles: {len(memory_board.conversation_memory['topic_struggles'])} topics")

            print("\n" + "=" * 60)
            print("DEMO READY!")
            print("=" * 60)
            print("\nThe avatar will now have access to this comprehensive memory during conversations.")
            print("Try asking the avatar:")
            print('  • "What mistakes do I often make?"')
            print('  • "What should I focus on improving?"')
            print('  • "How is my pronunciation?"')
            print('  • "Tell me about my reading progress"')
            print('  • "What grammar errors do I make?"')
            print("\nThe avatar will reference this memory board to provide personalized feedback!")

        except Exception as e:
            print(f"\n❌ Error creating demo memory: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            sys.exit(1)


if __name__ == '__main__':
    create_demo_memory()
