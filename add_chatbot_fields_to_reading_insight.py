"""
Migration script to add chatbot tracking fields to reading_memory_insight table.
Run this script to update the database schema.
"""

from app import create_app, db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_chatbot_fields():
    """Add chatbot tracking fields to reading_memory_insight table"""

    app = create_app()

    with app.app_context():
        try:
            # Check if table exists
            result = db.session.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='reading_memory_insight'
            """))

            if not result.fetchone():
                logger.error("Table reading_memory_insight does not exist!")
                return

            # Check if columns already exist
            result = db.session.execute(text("PRAGMA table_info(reading_memory_insight)"))
            columns = [row[1] for row in result.fetchall()]

            columns_to_add = []

            if 'chatbot_questions_asked' not in columns:
                columns_to_add.append(('chatbot_questions_asked', 'JSON'))
            if 'chatbot_topics_confused' not in columns:
                columns_to_add.append(('chatbot_topics_confused', 'JSON'))
            if 'chatbot_repeated_topics' not in columns:
                columns_to_add.append(('chatbot_repeated_topics', 'JSON'))

            if not columns_to_add:
                logger.info("✅ All chatbot fields already exist!")
                return

            # Add missing columns
            for column_name, column_type in columns_to_add:
                logger.info(f"Adding column: {column_name}")
                db.session.execute(text(f"""
                    ALTER TABLE reading_memory_insight
                    ADD COLUMN {column_name} {column_type}
                """))

            db.session.commit()
            logger.info(f"✅ Successfully added {len(columns_to_add)} chatbot tracking fields!")

            # Verify
            result = db.session.execute(text("PRAGMA table_info(reading_memory_insight)"))
            all_columns = [row[1] for row in result.fetchall()]
            logger.info(f"Current columns: {', '.join(all_columns)}")

        except Exception as e:
            logger.error(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    add_chatbot_fields()
