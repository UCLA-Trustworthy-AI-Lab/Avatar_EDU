from flask import Blueprint, render_template, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import os

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@bp.route('/login')
def login_page():
    """Login page"""
    return render_template('login.html')

@bp.route('/reading')
def reading_interface():
    """Interactive reading interface"""
    return render_template('reading.html')

@bp.route('/conversation')
def conversation_interface():
    """Avatar conversation interface"""
    return render_template('conversation.html')

@bp.route('/speaking')
def speaking_interface():
    """Speaking practice interface"""
    return render_template('speaking.html')

@bp.route('/listening')
def listening_interface():
    """Listening practice interface"""
    return render_template('listening.html')

@bp.route('/writing')
def writing_interface():
    """Writing practice interface"""
    return render_template('writing.html')

@bp.route('/dashboard')
def dashboard():
    """User dashboard - redirect to homepage for now"""
    return render_template('index.html')

@bp.route('/logout')
def logout():
    """Logout page - redirect to homepage for now"""
    return render_template('index.html')

@bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'language-arts-agent',
        'version': '0.1.0'
    })

@bp.route('/api/status')
@jwt_required()
def api_status():
    """API status for authenticated users"""
    user_id = get_jwt_identity()
    return jsonify({
        'status': 'authenticated',
        'user_id': user_id,
        'available_modules': ['reading', 'speaking', 'listening', 'writing', 'conversation']
    })

@bp.route('/samples/<filename>')
def serve_sample_files(filename):
    """Serve sample content files"""
    try:
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        samples_dir = os.path.join(project_root, 'samples')
        file_path = os.path.join(samples_dir, filename)

        # Security check - ensure file is within samples directory
        if not file_path.startswith(samples_dir):
            return jsonify({'error': 'Invalid file path'}), 400

        if os.path.exists(file_path):
            return send_file(file_path, mimetype='application/json')
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500