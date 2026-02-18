'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { Button } from './Button';

interface AudioRecorderProps {
  onAudioRecorded: (audioBlob: Blob) => void;
  onTranscriptionReceived?: (text: string) => void;
  isRecording?: boolean;
  disabled?: boolean;
}

export const AudioRecorder: React.FC<AudioRecorderProps> = ({
  onAudioRecorded,
  onTranscriptionReceived,
  isRecording: externalIsRecording,
  disabled = false
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [browserSupported, setBrowserSupported] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  
  // Check browser support on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const isSupported = !!(navigator && navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
      const isSecureContext = window.location.protocol === 'https:' || 
                             window.location.hostname === 'localhost' || 
                             window.location.hostname === '127.0.0.1' ||
                             window.location.hostname.includes('localhost');
      
      // Allow bypassing HTTPS check for development
      const bypassHttpsCheck = process.env.NEXT_PUBLIC_BYPASS_HTTPS_CHECK === 'true';
      const finalSecureContext = isSecureContext || bypassHttpsCheck;
      
      setBrowserSupported(isSupported && finalSecureContext);
    }
  }, []);

  const startRecording = useCallback(async () => {
    try {
      // Check if we're in a browser environment
      if (typeof window === 'undefined') {
        throw new Error('Not in browser environment');
      }
      
      // Check if running on HTTPS or localhost
      const isSecureContext = window.location.protocol === 'https:' || 
                             window.location.hostname === 'localhost' || 
                             window.location.hostname === '127.0.0.1' ||
                             window.location.hostname.includes('localhost');
      
      // Allow bypassing HTTPS check for development
      const bypassHttpsCheck = process.env.NEXT_PUBLIC_BYPASS_HTTPS_CHECK === 'true';
      
      if (!isSecureContext && !bypassHttpsCheck) {
        throw new Error('Audio recording requires HTTPS or localhost. Current URL: ' + window.location.href);
      }
      
      // Check if navigator.mediaDevices is available
      if (!navigator || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('MediaDevices API not supported in this browser. Try Chrome, Firefox, or Safari.');
      }
      
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 44100, // Higher sample rate for better quality
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      
      streamRef.current = stream;
      
      // Check available MIME types
      const mimeTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4',
        'audio/mpeg',
        'audio/wav'
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

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: selectedMimeType });

        if (audioBlob.size > 0) {
          onAudioRecorded(audioBlob);
        } else {
          console.error('Empty audio blob created');
          alert('Recording failed - no audio data captured');
        }
        
        // Clean up stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
      };

      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
      };

      mediaRecorder.start(1000); // Collect data every 1 second for more stable recording
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      const err = error as any;
      if (err.name === 'NotAllowedError') {
        alert('Microphone access denied. Please allow microphone permissions and try again.');
      } else if (err.name === 'NotFoundError') {
        alert('No microphone found. Please check your audio devices.');
      } else {
        alert(`Error accessing microphone: ${err.message || 'Unknown error'}`);
      }
    }
  }, [onAudioRecorded]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  // Use external recording state if provided
  const currentlyRecording = externalIsRecording !== undefined ? externalIsRecording : isRecording;

  // Show browser compatibility warning
  if (!browserSupported) {
    return (
      <div className="flex items-center gap-3">
        <div className="px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm">
          ⚠️ Audio recording not supported. Please use HTTPS or check your browser.
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <Button
        onClick={toggleRecording}
        disabled={disabled || isAnalyzing}
        className={`px-4 py-2 rounded-full font-medium transition-all ${
          currentlyRecording
            ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
            : 'bg-blue-600 hover:bg-blue-700 text-white'
        }`}
      >
        {currentlyRecording ? (
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-white rounded-full animate-pulse"></div>
            Recording...
          </div>
        ) : (
          <div className="flex items-center gap-2">
            🎤 Start Recording
          </div>
        )}
      </Button>
      
      {isAnalyzing && (
        <div className="text-sm text-gray-600 flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          Analyzing speech...
        </div>
      )}
      
      {currentlyRecording && (
        <div className="text-sm text-red-600 flex items-center gap-2">
          <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse"></div>
          Recording in progress
        </div>
      )}
    </div>
  );
};

export default AudioRecorder;