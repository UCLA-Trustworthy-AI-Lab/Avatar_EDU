#!/usr/bin/env python3
"""
Setup script for Language Arts Agent
"""

import os
import sys
import secrets

def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_urlsafe(32)

def setup_environment():
    """Set up basic environment variables"""
    env_file = '.env'
    
    # Read current .env content
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Replace placeholder values with generated ones
    content = content.replace('your-secret-key-here', generate_secret_key())
    content = content.replace('your-jwt-secret-key-here', generate_secret_key())
    
    # Write back to .env
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ Generated secure secret keys in .env file")
    print("\n📝 Next steps:")
    print("1. Add your OpenAI API key to .env file (required for chatbot)")
    print("2. Add your WordsAPI key to .env file (get free key at https://rapidapi.com/dpventures/api/wordsapi)")
    print("3. Set up PostgreSQL database or use SQLite for development")
    print("4. Run: uv run python setup_db.py")
    print("5. Run: uv run python run.py")

if __name__ == "__main__":
    setup_environment()