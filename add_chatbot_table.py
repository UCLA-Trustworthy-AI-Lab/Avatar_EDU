#!/usr/bin/env python3
"""
Database Migration - Add ChatbotInteraction Table

This script adds the chatbot_interaction table to track AI assistant conversations.
Run this to complete the memory board chatbot integration.

Usage:
    python add_chatbot_table.py
"""

import os
import sys
from app import create_app, db
from app.models.reading import ChatbotInteraction
from config import config

def add_chatbot_table():
    """Create chatbot_interaction table in the database"""

    env = os.environ.get('FLASK_ENV', 'development')
    app = create_app(config[env])

    with app.app_context():
        print("=" * 60)
        print("ADDING CHATBOT INTERACTION TABLE")
        print("=" * 60)

        # Create table
        print("\nCreating chatbot_interaction table...")
        try:
            db.create_all()
            print("✓ Table created successfully!")

            # Verify table exists
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()

            if 'chatbot_interaction' in tables:
                print("  ✓ chatbot_interaction")

                # Show columns
                columns = inspector.get_columns('chatbot_interaction')
                print("\n  Columns:")
                for col in columns:
                    print(f"    - {col['name']} ({col['type']})")

            else:
                print("  ✗ chatbot_interaction - NOT FOUND")
                sys.exit(1)

            print("\n" + "=" * 60)
            print("CHATBOT TABLE SETUP COMPLETE")
            print("=" * 60)
            print("\nThe chatbot memory integration is now ready!")
            print("\nFeatures:")
            print("  • Tracks what students ask the AI chatbot")
            print("  • Identifies topics they're confused about")
            print("  • Detects repeated questions")
            print("  • Chatbot responses now use memory context")
            print("\nHow it works:")
            print("  1. Student asks chatbot a question")
            print("  2. System loads their memory board")
            print("  3. Chatbot response is personalized based on past struggles")
            print("  4. Interaction is saved for memory extraction")
            print("  5. At session end, chatbot questions feed into memory")
            print("\nTest it:")
            print("  - Start a reading session")
            print("  - Ask the chatbot a question")
            print("  - Complete the session")
            print("  - Check memory board for chatbot insights!")

        except Exception as e:
            print(f"\n✗ Error creating table: {e}")
            sys.exit(1)


if __name__ == '__main__':
    add_chatbot_table()
