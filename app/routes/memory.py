"""
Memory Board Routes

API endpoints for accessing student memory board across all modules.
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.memory_service import get_memory_service
import logging

bp = Blueprint('memory', __name__, url_prefix='/api/memory')
logger = logging.getLogger(__name__)


@bp.route('/board', methods=['GET'])
@jwt_required()
def get_memory_board():
    """
    Get the student's comprehensive memory board from all modules.

    Returns:
        JSON object with memory data from all 5 modules:
        - reading_memory
        - listening_memory
        - speaking_memory
        - writing_memory
        - conversation_memory
        - overall_patterns
    """
    try:
        student_id = int(get_jwt_identity())
        memory_service = get_memory_service()

        # Get memory board
        memory_board = memory_service.get_or_create_memory_board(student_id)

        # Build response
        response_data = {
            'success': True,
            'memory_board': {
                'reading_memory': memory_board.reading_memory or {},
                'listening_memory': memory_board.listening_memory or {},
                'speaking_memory': memory_board.speaking_memory or {},
                'writing_memory': memory_board.writing_memory or {},
                'conversation_memory': memory_board.conversation_memory or {},
                'overall_patterns': memory_board.overall_patterns or {},
                'last_updated': memory_board.updated_at.isoformat() if memory_board.updated_at else None
            }
        }

        logger.info(f"Memory board retrieved for student {student_id}")
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error retrieving memory board: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve memory board'
        }), 500


@bp.route('/reading', methods=['GET'])
@jwt_required()
def get_reading_memory():
    """Get reading module memory only"""
    try:
        student_id = int(get_jwt_identity())
        memory_service = get_memory_service()

        reading_memory = memory_service.get_reading_memory(student_id)

        return jsonify({
            'success': True,
            'reading_memory': reading_memory
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving reading memory: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve reading memory'
        }), 500


@bp.route('/listening', methods=['GET'])
@jwt_required()
def get_listening_memory():
    """Get listening module memory only"""
    try:
        student_id = int(get_jwt_identity())
        memory_service = get_memory_service()

        listening_memory = memory_service.get_listening_memory(student_id)

        return jsonify({
            'success': True,
            'listening_memory': listening_memory
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving listening memory: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve listening memory'
        }), 500


@bp.route('/speaking', methods=['GET'])
@jwt_required()
def get_speaking_memory():
    """Get speaking module memory only"""
    try:
        student_id = int(get_jwt_identity())
        memory_service = get_memory_service()

        speaking_memory = memory_service.get_speaking_memory(student_id)

        return jsonify({
            'success': True,
            'speaking_memory': speaking_memory
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving speaking memory: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve speaking memory'
        }), 500


@bp.route('/writing', methods=['GET'])
@jwt_required()
def get_writing_memory():
    """Get writing module memory only"""
    try:
        student_id = int(get_jwt_identity())
        memory_service = get_memory_service()

        writing_memory = memory_service.get_writing_memory(student_id)

        return jsonify({
            'success': True,
            'writing_memory': writing_memory
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving writing memory: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve writing memory'
        }), 500


@bp.route('/conversation', methods=['GET'])
@jwt_required()
def get_conversation_memory():
    """Get conversation module memory only"""
    try:
        student_id = int(get_jwt_identity())
        memory_service = get_memory_service()

        conversation_memory = memory_service.get_conversation_memory(student_id)

        return jsonify({
            'success': True,
            'conversation_memory': conversation_memory
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving conversation memory: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve conversation memory'
        }), 500
