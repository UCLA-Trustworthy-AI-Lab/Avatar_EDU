import azure.cognitiveservices.speech as speechsdk
import json
import tempfile
from typing import Dict, Optional
from flask import current_app

class AzureSpeechClient:
    def __init__(self):
        self.speech_config = None
        self._initialize_config()

    def _initialize_config(self):
        """Initialize speech config within application context"""
        try:
            self.speech_key = current_app.config.get('AZURE_SPEECH_KEY')
            self.service_region = current_app.config.get('AZURE_SPEECH_REGION')

            if self.speech_key and self.service_region:
                self.speech_config = speechsdk.SpeechConfig(
                    subscription=self.speech_key,
                    region=self.service_region
                )
                self.speech_config.speech_recognition_language = "en-US"
        except RuntimeError:
            # Working outside application context, will initialize later
            self.speech_key = None
            self.service_region = None

    def _ensure_config(self):
        """Ensure speech config is initialized"""
        if self.speech_config is None and hasattr(current_app, 'config'):
            self._initialize_config()
    
    def speech_to_text(self, audio_file_path: str) -> str:
        self._ensure_config()
        if not self.speech_config:
            return "Azure Speech service not configured"
        
        try:
            audio_input = speechsdk.AudioConfig(filename=audio_file_path)
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_input
            )
            
            result = speech_recognizer.recognize_once_async().get()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                return "No speech could be recognized"
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                return f"Speech recognition canceled: {cancellation_details.reason}"
            
        except Exception as e:
            current_app.logger.error(f"Azure Speech-to-Text error: {str(e)}")
            return f"Error processing audio: {str(e)}"
    
    def assess_pronunciation(self, audio_file_path: str, reference_text: str, enable_prosody: bool = False, enable_content: bool = False) -> Dict:
        self._ensure_config()
        if not self.speech_config:
            return {"error": "Azure Speech service not configured"}

        # Retry logic for temporary authentication issues
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Configure pronunciation assessment
                pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                    reference_text=reference_text,
                    grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
                    granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
                    enable_miscue=True
                )

                audio_config = speechsdk.AudioConfig(filename=audio_file_path)
                speech_recognizer = speechsdk.SpeechRecognizer(
                    speech_config=self.speech_config,
                    audio_config=audio_config
                )

                pronunciation_config.apply_to(speech_recognizer)

                result = speech_recognizer.recognize_once_async().get()

                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    pronunciation_result = speechsdk.PronunciationAssessmentResult(result)

                    return {
                        "AccuracyScore": pronunciation_result.accuracy_score,
                        "FluencyScore": pronunciation_result.fluency_score,
                        "CompletenessScore": pronunciation_result.completeness_score,
                        "PronScore": pronunciation_result.pronunciation_score,
                        "Words": self._extract_word_details(result),
                        "RecognizedText": result.text
                    }
                elif result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = result.cancellation_details
                    error_details = f"Recognition canceled - Reason: {cancellation_details.reason}"
                    if cancellation_details.error_details:
                        error_details += f", Error: {cancellation_details.error_details}"

                    # Check if it's an authentication error and retry
                    if attempt < max_retries - 1 and ("401" in str(cancellation_details.error_details) or "Authentication error" in str(cancellation_details.error_details)):
                        current_app.logger.warning(f"Azure authentication error on attempt {attempt + 1}, retrying...")
                        # Reinitialize config and retry
                        self._initialize_config()
                        import time
                        time.sleep(1)  # Brief delay before retry
                        continue

                    current_app.logger.error(f"Azure cancellation details: {error_details}")
                    return {"error": error_details}
                else:
                    if attempt < max_retries - 1:
                        current_app.logger.warning(f"Recognition failed with reason {result.reason} on attempt {attempt + 1}, retrying...")
                        import time
                        time.sleep(1)
                        continue
                    return {"error": f"Recognition failed: {result.reason}"}

            except Exception as e:
                if attempt < max_retries - 1:
                    current_app.logger.warning(f"Azure assessment attempt {attempt + 1} failed: {str(e)}, retrying...")
                    import time
                    time.sleep(1)
                    continue
                current_app.logger.error(f"Azure Pronunciation Assessment error: {str(e)}")
                return {"error": f"Pronunciation assessment failed: {str(e)}"}

        return {"error": "All retry attempts failed"}
    
    def _extract_word_details(self, result) -> list:
        word_details = []
        try:
            # Parse the detailed result JSON
            json_result = json.loads(result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult))
            
            for word in json_result.get('NBest', [{}])[0].get('Words', []):
                word_details.append({
                    'Word': word.get('Word'),
                    'AccuracyScore': word.get('PronunciationAssessment', {}).get('AccuracyScore'),
                    'ErrorType': word.get('PronunciationAssessment', {}).get('ErrorType'),
                    'Phonemes': [
                        {
                            'Phoneme': phoneme.get('Phoneme'),
                            'AccuracyScore': phoneme.get('PronunciationAssessment', {}).get('AccuracyScore')
                        }
                        for phoneme in word.get('Phonemes', [])
                    ]
                })
        except:
            pass
        
        return word_details
    
    def text_to_speech(self, text: str, output_file_path: str, voice_name: str = "en-US-JennyNeural") -> bool:
        self._ensure_config()
        if not self.speech_config:
            return False
        
        try:
            self.speech_config.speech_synthesis_voice_name = voice_name
            audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file_path)
            
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            result = synthesizer.speak_text_async(text).get()
            
            return result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted
            
        except Exception as e:
            current_app.logger.error(f"Azure Text-to-Speech error: {str(e)}")
            return False
    
    def get_available_voices(self) -> list:
        self._ensure_config()
        if not self.speech_config:
            return []
        
        try:
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
            result = synthesizer.get_voices_async().get()
            
            if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
                return [
                    {
                        'name': voice.short_name,
                        'display_name': voice.local_name,
                        'gender': voice.gender.name,
                        'locale': voice.locale
                    }
                    for voice in result.voices
                    if voice.locale.startswith('en-')  # English voices only
                ]
            
        except Exception as e:
            current_app.logger.error(f"Error getting voices: {str(e)}")
        
        return []
    
    def create_ssml_content(self, text: str, voice_name: str = "en-US-JennyNeural", 
                          rate: str = "medium", pitch: str = "medium") -> str:
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{voice_name}">
                <prosody rate="{rate}" pitch="{pitch}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        return ssml.strip()