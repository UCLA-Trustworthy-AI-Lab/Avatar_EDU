"""
Migration script to add pronunciation tracking fields to conversation_memory_insight table.
Run this script to update the database schema.
"""

from app import create_app, db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_pronunciation_fields():
    """Add pronunciation tracking fields to conversation_memory_insight table"""

    app = create_app()

    with app.app_context():
        try:
            # Check if table exists
            result = db.session.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='conversation_memory_insight'
            """))

            if not result.fetchone():
                logger.info("Table conversation_memory_insight does not exist yet. Skipping migration.")
                return

            # Check if columns already exist
            result = db.session.execute(text("PRAGMA table_info(conversation_memory_insight)"))
            columns = [row[1] for row in result.fetchall()]

            columns_to_add = []

            if 'mispronounced_words' not in columns:
                columns_to_add.append(('mispronounced_words', 'JSON'))
            if 'phoneme_errors' not in columns:
                columns_to_add.append(('phoneme_errors', 'JSON'))
            if 'pronunciation_scores' not in columns:
                columns_to_add.append(('pronunciation_scores', 'JSON'))
            if 'topic_struggles' not in columns:
                columns_to_add.append(('topic_struggles', 'JSON'))
            if 'total_messages' not in columns:
                columns_to_add.append(('total_messages', 'INTEGER DEFAULT 0'))
            if 'total_words' not in columns:
                columns_to_add.append(('total_words', 'INTEGER DEFAULT 0'))
            if 'avg_words_per_message' not in columns:
                columns_to_add.append(('avg_words_per_message', 'REAL DEFAULT 0.0'))

            if not columns_to_add:
                logger.info("✅ All pronunciation fields already exist!")
                return

            # Add missing columns
            for column_name, column_type in columns_to_add:
                logger.info(f"Adding column: {column_name}")
                db.session.execute(text(f"""
                    ALTER TABLE conversation_memory_insight
                    ADD COLUMN {column_name} {column_type}
                """))

            db.session.commit()
            logger.info(f"✅ Successfully added {len(columns_to_add)} pronunciation tracking fields!")

            # Verify
            result = db.session.execute(text("PRAGMA table_info(conversation_memory_insight)"))
            all_columns = [row[1] for row in result.fetchall()]
            logger.info(f"Current columns: {', '.join(all_columns)}")

        except Exception as e:
            logger.error(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    add_pronunciation_fields()
