#!/usr/bin/env python3
"""
Database Migration Script - Add Memory Board Tables

This script adds the new memory board tables to the existing database.
Run this after implementing the memory board feature.

Usage:
    python setup_memory_tables.py
"""

import os
import sys
from app import create_app, db
from app.models.memory import (
    StudentMemoryBoard, ReadingMemoryInsight, ListeningMemoryInsight,
    SpeakingMemoryInsight, WritingMemoryInsight, ConversationMemoryInsight
)
from config import config

def setup_memory_tables():
    """Create memory board tables in the database"""

    # Get app with appropriate config
    env = os.environ.get('FLASK_ENV', 'development')
    app = create_app(config[env])

    with app.app_context():
        print("=" * 60)
        print("MEMORY BOARD TABLE SETUP")
        print("=" * 60)

        # Create tables
        print("\nCreating memory board tables...")
        try:
            db.create_all()
            print("✓ Tables created successfully!")

            # Verify tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()

            memory_tables = [
                'student_memory_board',
                'reading_memory_insight',
                'listening_memory_insight',
                'speaking_memory_insight',
                'writing_memory_insight',
                'conversation_memory_insight'
            ]

            print("\nVerifying tables:")
            for table in memory_tables:
                if table in tables:
                    print(f"  ✓ {table}")
                else:
                    print(f"  ✗ {table} - NOT FOUND")

            print("\n" + "=" * 60)
            print("MEMORY BOARD SETUP COMPLETE")
            print("=" * 60)
            print("\nThe memory board feature is now ready to use!")
            print("\nKey features:")
            print("  • Tracks student mistakes and patterns")
            print("  • Adapts questions based on weak areas")
            print("  • Compresses insights using GPT-4")
            print("  • Provides personalized learning experience")
            print("\nAPI Endpoints:")
            print("  GET  /api/reading/memory-board - View memory board")
            print("  POST /api/reading/memory-board/compress - Force compression")
            print("  GET  /api/reading/memory-board/insights - View recent insights")

        except Exception as e:
            print(f"\n✗ Error creating tables: {e}")
            sys.exit(1)


if __name__ == '__main__':
    setup_memory_tables()
