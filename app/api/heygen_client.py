import requests
import json
import time
import uuid
from typing import Dict, Optional, Any
from flask import current_app
import logging

class HeyGenClient:
    def __init__(self):
        self.api_key = current_app.config.get('HEYGEN_API_KEY')
        self.base_url = "https://api.heygen.com/v2"
        self.streaming_url = "https://api.heygen.com/v1"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        self.logger = logging.getLogger(__name__)
    
    def create_video(self, script: str, avatar_id: str = None, voice_id: str = None) -> Dict:
        if not self.api_key:
            return {"error": "HeyGen API key not configured"}
        
        # Default child-friendly avatar and voice
        default_avatar = avatar_id or "anna_public_3_20240108"
        default_voice = voice_id or "1bd001e7e50f421d891986aad5158bc8"
        
        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": default_avatar,
                        "avatar_style": "normal"
                    },
                    "voice": {
                        "type": "text",
                        "input_text": script,
                        "voice_id": default_voice
                    },
                    "background": {
                        "type": "color",
                        "value": "#000000"
                    }
                }
            ],
            "dimension": {
                "width": 1280,
                "height": 720
            },
            "aspect_ratio": None,
            "test": current_app.config.get('FLASK_ENV') == 'development'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/video/generate",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "video_id": result.get("data", {}).get("video_id"),
                    "status": "generating",
                    "message": "Video generation started"
                }
            else:
                error_msg = response.json().get("message", "Unknown error")
                return {"error": f"HeyGen API error: {error_msg}"}
                
        except requests.exceptions.Timeout:
            return {"error": "Request timeout - HeyGen service unavailable"}
        except Exception as e:
            current_app.logger.error(f"HeyGen API error: {str(e)}")
            return {"error": f"Failed to create video: {str(e)}"}
    
    def get_video_status(self, video_id: str) -> Dict:
        if not self.api_key or not video_id:
            return {"error": "Missing API key or video ID"}
        
        try:
            response = requests.get(
                f"{self.base_url}/video/status",
                headers=self.headers,
                params={"video_id": video_id},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                return {
                    "video_id": video_id,
                    "status": data.get("status"),
                    "video_url": data.get("video_url"),
                    "thumbnail_url": data.get("thumbnail_url"),
                    "duration": data.get("duration"),
                    "created_at": data.get("created_at")
                }
            else:
                error_msg = response.json().get("message", "Unknown error")
                return {"error": f"Status check failed: {error_msg}"}
                
        except Exception as e:
            current_app.logger.error(f"HeyGen status check error: {str(e)}")
            return {"error": f"Failed to check video status: {str(e)}"}
    
    def wait_for_video_completion(self, video_id: str, max_wait_time: int = 300) -> Dict:
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status_result = self.get_video_status(video_id)
            
            if "error" in status_result:
                return status_result
            
            status = status_result.get("status")
            
            if status == "completed":
                return status_result
            elif status == "failed":
                return {"error": "Video generation failed"}
            
            time.sleep(10)  # Wait 10 seconds before checking again
        
        return {"error": "Video generation timeout"}
    
    def get_available_avatars(self) -> list:
        if not self.api_key:
            return []
        
        try:
            response = requests.get(
                f"{self.base_url}/avatars",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                avatars = result.get("data", {}).get("avatars", [])
                
                # Filter for child-appropriate avatars
                child_friendly_avatars = []
                for avatar in avatars:
                    if self._is_child_appropriate_avatar(avatar):
                        child_friendly_avatars.append({
                            "avatar_id": avatar.get("avatar_id"),
                            "name": avatar.get("name"),
                            "preview_image": avatar.get("preview_image_url"),
                            "gender": avatar.get("gender")
                        })
                
                return child_friendly_avatars
            
        except Exception as e:
            current_app.logger.error(f"Error fetching avatars: {str(e)}")
        
        return []
    
    def get_available_voices(self) -> list:
        if not self.api_key:
            return []
        
        try:
            response = requests.get(
                f"{self.base_url}/voices",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                voices = result.get("data", {}).get("voices", [])
                
                # Filter for English, child-appropriate voices
                child_friendly_voices = []
                for voice in voices:
                    if (voice.get("language") == "English" and 
                        self._is_child_appropriate_voice(voice)):
                        child_friendly_voices.append({
                            "voice_id": voice.get("voice_id"),
                            "name": voice.get("name"),
                            "gender": voice.get("gender"),
                            "age": voice.get("age"),
                            "preview_audio": voice.get("preview_audio_url")
                        })
                
                return child_friendly_voices
            
        except Exception as e:
            current_app.logger.error(f"Error fetching voices: {str(e)}")
        
        return []
    
    def _is_child_appropriate_avatar(self, avatar: Dict) -> bool:
        # Filter criteria for child-appropriate avatars
        name = avatar.get("name", "").lower()
        
        # Exclude inappropriate content
        inappropriate_keywords = ["sexy", "adult", "mature", "provocative"]
        if any(keyword in name for keyword in inappropriate_keywords):
            return False
        
        # Prefer friendly, professional, or educational avatars
        appropriate_keywords = ["teacher", "friendly", "professional", "young", "student"]
        if any(keyword in name for keyword in appropriate_keywords):
            return True
        
        # Default to include if no obvious issues
        return True
    
    def _is_child_appropriate_voice(self, voice: Dict) -> bool:
        # Filter for child-appropriate voices
        age = voice.get("age", "").lower()
        gender = voice.get("gender", "").lower()
        
        # Prefer younger-sounding or neutral voices
        appropriate_ages = ["young", "child", "teen", "neutral"]
        if any(age_term in age for age_term in appropriate_ages):
            return True
        
        # Exclude mature or overly adult voices
        inappropriate_ages = ["mature", "elderly", "deep", "sultry"]
        if any(age_term in age for age_term in inappropriate_ages):
            return False
        
        return True
    
    def create_educational_video(self, lesson_content: Dict) -> Dict:
        # Create specialized educational content with HeyGen
        script = self._format_educational_script(lesson_content)
        
        # Use educational-friendly settings
        result = self.create_video(
            script=script,
            avatar_id=lesson_content.get("preferred_avatar"),
            voice_id=lesson_content.get("preferred_voice")
        )
        
        return result
    
    def _format_educational_script(self, lesson_content: Dict) -> str:
        # Format lesson content into a natural script for the avatar
        title = lesson_content.get("title", "")
        content = lesson_content.get("content", "")
        key_points = lesson_content.get("key_points", [])
        
        script = f"Hello! Today we're going to learn about {title}. "
        script += content + " "
        
        if key_points:
            script += "Let's remember these important points: "
            for i, point in enumerate(key_points, 1):
                script += f"{i}. {point}. "
        
        script += "Great job learning with me today!"
        
        return script
    
    # ===================
    # STREAMING API METHODS
    # ===================
    
    def create_streaming_token(self) -> Dict[str, Any]:
        """Create a streaming token for real-time avatar conversations"""
        if not self.api_key:
            return {"error": "HeyGen API key not configured"}
        
        try:
            response = requests.post(
                f"{self.streaming_url}/streaming.create_token",
                headers={"x-api-key": self.api_key},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "token": result.get("data", {}).get("token"),
                    "expires_at": result.get("data", {}).get("expires_at"),
                    "status": "success"
                }
            else:
                error_msg = response.json().get("message", "Unknown error")
                self.logger.error(f"Failed to create streaming token: {error_msg}")
                return {"error": f"Token creation failed: {error_msg}"}
                
        except Exception as e:
            self.logger.error(f"Streaming token creation error: {str(e)}")
            return {"error": f"Failed to create streaming token: {str(e)}"}
    
    def start_streaming_session(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Start a streaming avatar session"""
        if not self.api_key:
            return {"error": "HeyGen API key not configured"}
        
        default_config = {
            "quality": "medium",
            "avatar_name": "Anna_public_3_20240108", 
            "voice": {
                "voice_id": "1bd001e7e50f421d891986aad5158bc8",
                "rate": 1.0,
                "emotion": "friendly"
            },
            "background": {
                "type": "color",
                "value": "#000000"
            },
            "ratio": "16:9",
            "language": "en"
        }
        
        # Merge user config with defaults
        session_config = {**default_config, **config}
        
        try:
            response = requests.post(
                f"{self.streaming_url}/streaming.start",
                headers=self.headers,
                json=session_config,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "session_id": result.get("data", {}).get("session_id"),
                    "stream_url": result.get("data", {}).get("stream_url"),
                    "sdp": result.get("data", {}).get("sdp"),
                    "ice_servers": result.get("data", {}).get("ice_servers", []),
                    "status": "started"
                }
            else:
                error_msg = response.json().get("message", "Unknown error")
                self.logger.error(f"Failed to start streaming session: {error_msg}")
                return {"error": f"Session start failed: {error_msg}"}
                
        except Exception as e:
            self.logger.error(f"Streaming session start error: {str(e)}")
            return {"error": f"Failed to start streaming session: {str(e)}"}
    
    def send_streaming_message(self, session_id: str, message: str, session_info: Dict = None) -> Dict[str, Any]:
        """Send a message to the streaming avatar"""
        if not self.api_key or not session_id:
            return {"error": "Missing API key or session ID"}
        
        payload = {
            "session_id": session_id,
            "text": message,
            "task_type": "talk",
            "task_mode": "sync"
        }
        
        # Add session info if provided
        if session_info:
            payload.update(session_info)
        
        try:
            response = requests.post(
                f"{self.streaming_url}/streaming.task",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "task_id": result.get("data", {}).get("task_id"),
                    "status": "sent",
                    "message": "Message sent to avatar"
                }
            else:
                error_msg = response.json().get("message", "Unknown error")
                self.logger.error(f"Failed to send streaming message: {error_msg}")
                return {"error": f"Message send failed: {error_msg}"}
                
        except Exception as e:
            self.logger.error(f"Streaming message send error: {str(e)}")
            return {"error": f"Failed to send message: {str(e)}"}
    
    def stop_streaming_session(self, session_id: str) -> Dict[str, Any]:
        """Stop a streaming avatar session"""
        if not self.api_key or not session_id:
            return {"error": "Missing API key or session ID"}
        
        try:
            response = requests.post(
                f"{self.streaming_url}/streaming.stop",
                headers=self.headers,
                json={"session_id": session_id},
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "status": "stopped",
                    "message": "Streaming session stopped successfully"
                }
            else:
                error_msg = response.json().get("message", "Unknown error")
                self.logger.error(f"Failed to stop streaming session: {error_msg}")
                return {"error": f"Session stop failed: {error_msg}"}
                
        except Exception as e:
            self.logger.error(f"Streaming session stop error: {str(e)}")
            return {"error": f"Failed to stop streaming session: {str(e)}"}
    
    def get_streaming_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about a streaming session"""
        if not self.api_key or not session_id:
            return {"error": "Missing API key or session ID"}
        
        try:
            response = requests.get(
                f"{self.streaming_url}/streaming.info",
                headers=self.headers,
                params={"session_id": session_id},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                return {
                    "session_id": session_id,
                    "status": data.get("status"),
                    "duration": data.get("duration"),
                    "messages_count": data.get("messages_count"),
                    "created_at": data.get("created_at"),
                    "avatar_config": data.get("avatar_config", {})
                }
            else:
                error_msg = response.json().get("message", "Unknown error")
                return {"error": f"Session info failed: {error_msg}"}
                
        except Exception as e:
            self.logger.error(f"Streaming session info error: {str(e)}")
            return {"error": f"Failed to get session info: {str(e)}"}
    
    def create_conversation_session(self, user_id: int, topic: str = "general") -> Dict[str, Any]:
        """Create a complete conversation session for education"""
        try:
            # Step 1: Create streaming token
            token_result = self.create_streaming_token()
            if "error" in token_result:
                return token_result
            
            # Step 2: Configure session for educational conversation
            conversation_config = {
                "quality": "high",
                "avatar_name": "Anna_public_3_20240108",  # Professional female avatar
                "voice": {
                    "voice_id": "1bd001e7e50f421d891986aad5158bc8",  # Clear English voice
                    "rate": 0.9,  # Slightly slower for learning
                    "emotion": "friendly"
                },
                "background": {
                    "type": "color", 
                    "value": "#000000"  # Black background
                },
                "ratio": "16:9",
                "language": "en",
                "conversation_topic": topic,
                "user_id": user_id
            }
            
            # Step 3: Start streaming session
            session_result = self.start_streaming_session(conversation_config)
            if "error" in session_result:
                return session_result
            
            # Step 4: Send welcome message
            welcome_messages = {
                "general": "Hello! I'm so excited to have a conversation with you in English today. What would you like to talk about?",
                "daily_life": "Hi there! Let's chat about daily life. How has your day been going? I'd love to hear about it!",
                "academic": "Welcome! I'm here to help you practice academic English. What subject are you studying, or what academic topic interests you?",
                "business": "Hello! Let's practice professional English together. Are you interested in any particular industry or business topic?",
                "travel": "Hi! Let's talk about travel and culture. Have you been anywhere interesting lately, or is there somewhere you'd love to visit?"
            }
            
            welcome_text = welcome_messages.get(topic, welcome_messages["general"])
            
            # Send initial message
            message_result = self.send_streaming_message(
                session_result["session_id"], 
                welcome_text,
                {"conversation_start": True, "topic": topic}
            )
            
            return {
                "session_id": session_result["session_id"],
                "token": token_result["token"], 
                "stream_url": session_result.get("stream_url"),
                "sdp": session_result.get("sdp"),
                "ice_servers": session_result.get("ice_servers", []),
                "welcome_message": welcome_text,
                "topic": topic,
                "status": "ready"
            }
            
        except Exception as e:
            self.logger.error(f"Conversation session creation error: {str(e)}")
            return {"error": f"Failed to create conversation session: {str(e)}"}
    
    def handle_conversation_turn(self, session_id: str, user_message: str, context: Dict = None) -> Dict[str, Any]:
        """Handle a conversation turn with educational context"""
        try:
            # Generate educational response based on user input
            response_text = self._generate_educational_response(user_message, context)
            
            # Send response to avatar
            result = self.send_streaming_message(session_id, response_text)
            
            if "error" not in result:
                result["response_text"] = response_text
                result["user_message"] = user_message
                result["conversation_analysis"] = self._analyze_conversation_turn(user_message, response_text)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Conversation turn error: {str(e)}")
            return {"error": f"Failed to handle conversation turn: {str(e)}"}
    
    def _generate_educational_response(self, user_message: str, context: Dict = None) -> str:
        """Generate educational avatar response"""
        # This is a simplified version - in production you'd integrate with OpenAI
        # For now, providing template responses for educational conversation
        
        message_lower = user_message.lower()
        
        # Encouraging responses for different scenarios
        if any(word in message_lower for word in ["hello", "hi", "hey"]):
            return "Hello! It's wonderful to meet you. How are you feeling about practicing English today?"
        
        elif any(word in message_lower for word in ["good", "fine", "okay", "well"]):
            return "That's great to hear! I'm here to help you feel comfortable speaking English. What topics do you enjoy talking about?"
        
        elif any(word in message_lower for word in ["study", "school", "university", "class"]):
            return "Studies are so important! What subject are you focusing on? I'd love to hear about what you're learning."
        
        elif any(word in message_lower for word in ["difficult", "hard", "challenging"]):
            return "I understand that learning can be challenging sometimes. That's completely normal! What specific area would you like to work on? I'm here to help you step by step."
        
        elif any(word in message_lower for word in ["like", "enjoy", "love"]):
            return "That sounds really interesting! Can you tell me more about why you like that? I'd love to learn more about your interests."
        
        elif "?" in user_message:
            return "That's a great question! Let me think about that with you. What are your thoughts on it? I'm curious to hear your perspective."
        
        else:
            return "That's really interesting! I can tell you're thinking deeply about this. Could you elaborate a bit more? I'm enjoying our conversation."
    
    def _analyze_conversation_turn(self, user_message: str, avatar_response: str) -> Dict[str, Any]:
        """Analyze conversation for learning insights"""
        try:
            word_count = len(user_message.split())
            sentence_count = user_message.count('.') + user_message.count('!') + user_message.count('?')
            
            # Basic complexity analysis
            complexity_indicators = ['because', 'although', 'however', 'therefore', 'moreover', 'furthermore']
            complexity_score = sum(1 for word in complexity_indicators if word in user_message.lower())
            
            # Question analysis
            has_question = '?' in user_message
            
            # Engagement indicators
            engagement_words = ['think', 'feel', 'believe', 'opinion', 'interested', 'excited']
            engagement_score = sum(1 for word in engagement_words if word in user_message.lower())
            
            return {
                "word_count": word_count,
                "sentence_count": max(1, sentence_count),
                "complexity_score": min(100, complexity_score * 20),
                "has_question": has_question,
                "engagement_level": "high" if engagement_score > 2 else "medium" if engagement_score > 0 else "low",
                "fluency_estimate": min(100, word_count * 3),
                "participation_score": min(100, (word_count + engagement_score) * 5)
            }
            
        except Exception as e:
            self.logger.error(f"Conversation analysis error: {str(e)}")
            return {}