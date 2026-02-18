import { useCallback, useRef, useState } from 'react';
import { useTextChat } from './useTextChat';
import { useConversationAnalytics } from './useConversationAnalytics';

interface WhisperVoiceChatOptions {
  onTranscriptionReceived?: (text: string) => void;
  onError?: (error: string) => void;
  onStatusChange?: (status: 'idle' | 'listening' | 'processing') => void;
}

export const useWhisperVoiceChat = (options?: WhisperVoiceChatOptions) => {
  const { sendMessage } = useTextChat();
  const { addVoiceAnalysis } = useConversationAnalytics();
  const [status, setStatus] = useState<'idle' | 'listening' | 'processing'>('idle');
  const [isEnabled, setIsEnabled] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const updateStatus = useCallback((newStatus: 'idle' | 'listening' | 'processing') => {
    setStatus(newStatus);
    options?.onStatusChange?.(newStatus);
  }, [options]);

  const processAudioWithWhisper = useCallback(async (audioBlob: Blob) => {
    try {
      updateStatus('processing');
      
      const formData = new FormData();
      formData.append('audio', audioBlob, 'voice-chat.webm');

      const response = await fetch('/api/test-whisper', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success && data.transcription) {
        // Notify about transcription
        options?.onTranscriptionReceived?.(data.transcription);
        
        // Send to avatar for response
        sendMessage(data.transcription);
        
        // Store voice analysis data (using timestamp as ID since we don't get message ID)
        const analysisId = `voice_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        addVoiceAnalysis(analysisId, {
          transcribedText: data.transcription,
          pronunciationScore: 85, // Could get from more detailed analysis
          analysisData: data,
          timestamp: new Date().toISOString()
        });
        
        return data.transcription;
      } else {
        const errorMsg = `Whisper failed: ${data.error}`;
        console.error(errorMsg, data);
        options?.onError?.(errorMsg);
        return null;
      }
    } catch (error) {
      const errorMsg = `Voice chat error: ${error instanceof Error ? error.message : 'Unknown error'}`;
      console.error(errorMsg);
      options?.onError?.(errorMsg);
      return null;
    } finally {
      updateStatus('idle');
    }
  }, [sendMessage, options, updateStatus]);

  const startListening = useCallback(async () => {
    if (!isEnabled) return;

    try {
      updateStatus('listening');

      // Check browser support and security context
      if (!navigator?.mediaDevices?.getUserMedia) {
        throw new Error('MediaDevices API not supported in this browser. Please use Chrome, Firefox, or Safari.');
      }

      // Check if we're in a secure context (HTTPS or localhost)
      const isSecureContext = window.isSecureContext || window.location.protocol === 'https:' || window.location.hostname === 'localhost';
      const bypassHttpsCheck = process.env.NEXT_PUBLIC_BYPASS_HTTPS_CHECK === 'true';
      
      if (!isSecureContext && !bypassHttpsCheck) {
        throw new Error('Microphone access requires HTTPS. Please use HTTPS or set NEXT_PUBLIC_BYPASS_HTTPS_CHECK=true in development.');
      }

      let stream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            sampleRate: 44100,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          }
        });
      } catch (micError: any) {
        // Provide more specific error messages
        if (micError.name === 'NotAllowedError') {
          throw new Error('Microphone permission denied. Please allow microphone access in your browser settings and try again.');
        } else if (micError.name === 'NotFoundError') {
          throw new Error('No microphone found. Please connect a microphone and try again.');
        } else if (micError.name === 'NotReadableError') {
          throw new Error('Microphone is already in use by another application. Please close other apps using the microphone.');
        } else {
          throw new Error(`Microphone access failed: ${micError.message || 'Unknown error'}`);
        }
      }

      streamRef.current = stream;

      // Find best supported MIME type
      const mimeTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4',
        'audio/mpeg'
      ];

      let selectedMimeType = 'audio/webm';
      for (const mimeType of mimeTypes) {
        if (MediaRecorder.isTypeSupported(mimeType)) {
          selectedMimeType = mimeType;
          break;
        }
      }

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: selectedMimeType
      });

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: selectedMimeType });
        
        if (audioBlob.size > 0) {
          await processAudioWithWhisper(audioBlob);
        }

        // Clean up stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
      };

      mediaRecorder.start();

    } catch (error) {
      const errorMsg = `Failed to start listening: ${error instanceof Error ? error.message : 'Unknown error'}`;
      console.error(errorMsg);
      options?.onError?.(errorMsg);
      updateStatus('idle');
    }
  }, [isEnabled, processAudioWithWhisper, options, updateStatus]);

  const stopListening = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const toggleListening = useCallback(() => {
    if (status === 'listening') {
      stopListening();
    } else if (status === 'idle') {
      startListening();
    }
  }, [status, startListening, stopListening]);

  const enableWhisperVoiceChat = useCallback((enabled: boolean) => {
    setIsEnabled(enabled);
    if (!enabled && status !== 'idle') {
      stopListening();
    }
  }, [status, stopListening]);

  return {
    // State
    status,
    isEnabled,
    isListening: status === 'listening',
    isProcessing: status === 'processing',
    
    // Actions
    startListening,
    stopListening,
    toggleListening,
    enableWhisperVoiceChat,
  };
};