"""
Migration script to update writing_memory_insight table with new fields.
Run this script to update the database schema.
"""

from app import create_app, db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_writing_fields():
    """Update writing_memory_insight table with new tracking fields"""

    app = create_app()

    with app.app_context():
        try:
            # Check if table exists
            result = db.session.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='writing_memory_insight'
            """))

            if not result.fetchone():
                logger.error("Table writing_memory_insight does not exist!")
                return

            # Check if columns already exist
            result = db.session.execute(text("PRAGMA table_info(writing_memory_insight)"))
            columns = [row[1] for row in result.fetchall()]

            columns_to_add = []

            # Add missing columns
            if 'sentence_issues' not in columns:
                columns_to_add.append(('sentence_issues', 'JSON'))
            if 'content_weaknesses' not in columns:
                columns_to_add.append(('content_weaknesses', 'JSON'))
            if 'overall_score' not in columns:
                columns_to_add.append(('overall_score', 'INTEGER'))
            if 'on_topic' not in columns:
                columns_to_add.append(('on_topic', 'BOOLEAN DEFAULT 1'))
            if 'learning_session_id' not in columns:
                columns_to_add.append(('learning_session_id', 'INTEGER'))
            if 'topic' not in columns:
                columns_to_add.append(('topic', 'TEXT'))

            # Rename session_id to learning_session_id if needed
            if 'session_id' in columns and 'learning_session_id' not in columns:
                logger.info("Note: 'session_id' exists but will be kept alongside 'learning_session_id'")

            if not columns_to_add:
                logger.info("✅ All writing fields already exist!")
                return

            # Add missing columns
            for column_name, column_type in columns_to_add:
                logger.info(f"Adding column: {column_name}")
                db.session.execute(text(f"""
                    ALTER TABLE writing_memory_insight
                    ADD COLUMN {column_name} {column_type}
                """))

            db.session.commit()
            logger.info(f"✅ Successfully added {len(columns_to_add)} writing tracking fields!")

            # Verify
            result = db.session.execute(text("PRAGMA table_info(writing_memory_insight)"))
            all_columns = [row[1] for row in result.fetchall()]
            logger.info(f"Current columns: {', '.join(all_columns)}")

        except Exception as e:
            logger.error(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    update_writing_fields()
