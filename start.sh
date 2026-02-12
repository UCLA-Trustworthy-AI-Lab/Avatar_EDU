#!/bin/bash

echo "🚀 Starting Language Arts Agent..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚙️  Setting up environment..."
    uv run python setup.py
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file and add your API keys:"
    echo "   - OPENAI_API_KEY (required for AI chatbot)"
    echo "   - WORDSAPI_KEY (get free key at https://rapidapi.com/dpventures/api/wordsapi)"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check if database exists
if [ ! -f language_arts.db ]; then
    echo "🗄️  Setting up database..."
    uv run python setup_db.py
fi

echo "🌐 Starting Flask application..."
echo "📍 Access the app at: http://localhost:5000"
echo "📖 Reading interface: http://localhost:5000/reading"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uv run python run.py