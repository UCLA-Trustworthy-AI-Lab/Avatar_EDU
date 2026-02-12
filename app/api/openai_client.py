from openai import OpenAI
import json
from typing import Dict, List, Optional
from flask import current_app

class OpenAIClient:
    def __init__(self):
        self.api_key = current_app.config.get('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
    
    def generate_content(self, prompt: str = "", model: str = "gpt-3.5-turbo", messages: List[Dict] = None, max_tokens: int = 1000, temperature: float = 0.7) -> Dict:
        try:
            if not self.client:
                return {"error": "OpenAI API key not configured"}
            
            # Use provided messages or create default structure
            if messages is None:
                messages = [
                    {"role": "system", "content": "You are a helpful educational assistant for high school and college students (ages 16-20) learning English. Provide appropriate, engaging, and educational content."},
                    {"role": "user", "content": prompt}
                ]
                
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON if it looks like JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"content": content}
                
        except Exception as e:
            current_app.logger.error(f"OpenAI API error: {str(e)}")
            return {"error": "Failed to generate content", "details": str(e)}
    
    def generate_questions(self, content: str, num_questions: int = 5, difficulty: str = "intermediate") -> List[Dict]:
        prompt = f"""
        Create {num_questions} educational questions based on this content for {difficulty} level students (ages 8-14):
        
        {content}
        
        Return as JSON array with this format:
        [
            {{
                "question": "Question text",
                "type": "multiple_choice",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "difficulty": "easy|medium|hard"
            }}
        ]
        """
        
        try:
            response = self.generate_content(prompt)
            if isinstance(response, dict) and "content" in response:
                return json.loads(response["content"])
            return response if isinstance(response, list) else []
        except:
            return []
    
    def evaluate_answer(self, question: str, correct_answer: str, student_answer: str) -> Dict:
        prompt = f"""
        Evaluate this student's answer (age 8-14):
        
        Question: {question}
        Correct Answer: {correct_answer}
        Student Answer: {student_answer}
        
        Provide:
        1. Score (0-100)
        2. Brief encouraging feedback
        3. Whether the answer demonstrates understanding
        
        Return as JSON.
        """
        
        return self.generate_content(prompt)
    
    def generate_writing_feedback(self, text: str, prompt: str = "") -> Dict:
        feedback_prompt = f"""
        Provide constructive writing feedback for this student work (ages 8-14):
        
        Original Prompt: {prompt}
        Student Writing: {text}
        
        Evaluate:
        1. Content and ideas (25 points)
        2. Organization (25 points) 
        3. Grammar and mechanics (25 points)
        4. Vocabulary and word choice (25 points)
        
        Provide encouraging feedback with specific suggestions for improvement.
        Return as JSON with scores and feedback.
        """
        
        return self.generate_content(feedback_prompt)
    
    def create_personalized_content(self, student_data: Dict, content_type: str) -> Dict:
        age = student_data.get('age', 10)
        interests = student_data.get('interests', [])
        difficulty_level = student_data.get('level', 'intermediate')
        
        prompt = f"""
        Create personalized {content_type} content for:
        - Age: {age}
        - Interests: {', '.join(interests) if interests else 'general topics'}
        - Level: {difficulty_level}
        
        Make it engaging, educational, and age-appropriate.
        Return structured content as JSON.
        """
        
        return self.generate_content(prompt)