'use client';

import { useState } from 'react';
import { Button } from './Button';
import { useWhisperVoiceChat } from './logic/useWhisperVoiceChat';

type VoiceChatMode = 'whisper' | 'disabled';

interface VoiceChatSelectorProps {
  onModeChange?: (mode: VoiceChatMode) => void;
}

export const VoiceChatSelector: React.FC<VoiceChatSelectorProps> = ({ onModeChange }) => {
  const [selectedMode, setSelectedMode] = useState<VoiceChatMode>('disabled');
  const [transcription, setTranscription] = useState<string>('');
  const [error, setError] = useState<string>('');

  const whisperVoiceChat = useWhisperVoiceChat({
    onTranscriptionReceived: (text) => {
      setTranscription(text);
      setError('');
    },
    onError: (errorMsg) => {
      setError(errorMsg);
      setTranscription('');
    },
    onStatusChange: (status) => {
    }
  });

  const handleModeChange = (mode: VoiceChatMode) => {
    setSelectedMode(mode);
    setTranscription('');
    setError('');
    
    // Enable/disable Whisper voice chat
    whisperVoiceChat.enableWhisperVoiceChat(mode === 'whisper');
    
    // Notify parent component
    onModeChange?.(mode);
  };

  const getModeDescription = (mode: VoiceChatMode) => {
    switch (mode) {
      case 'whisper':
        return 'Uses OpenAI Whisper for high-quality speech transcription and analysis';
      case 'disabled':
        return 'Voice chat disabled - text input only';
    }
  };

  const getModeIcon = (mode: VoiceChatMode) => {
    switch (mode) {
      case 'whisper':
        return '🎤';
      case 'disabled':
        return '⚪';
    }
  };

  return (
    <div className="space-y-4">
      {/* Mode Selection */}
      <div className="p-4 bg-gray-50 rounded-lg">
        <h3 className="font-medium text-gray-800 mb-3">Voice Chat Transport</h3>
        
        <div className="grid grid-cols-2 gap-2">
          {(['disabled', 'whisper'] as VoiceChatMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => handleModeChange(mode)}
              className={`p-3 rounded-lg text-left transition-all ${
                selectedMode === mode
                  ? 'bg-blue-100 border-2 border-blue-300 text-blue-800'
                  : 'bg-white border-2 border-gray-200 text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{getModeIcon(mode)}</span>
                <span className="font-medium capitalize">{mode} Transport</span>
                {selectedMode === mode && <span className="text-xs bg-blue-200 px-2 py-1 rounded">ACTIVE</span>}
              </div>
              <div className="text-xs text-gray-600">
                {getModeDescription(mode)}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Whisper Voice Chat Controls */}
      {selectedMode === 'whisper' && (
        <div className="p-4 bg-blue-50 rounded-lg border-2 border-blue-200">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-blue-800">🎤 Whisper Voice Chat</h4>
            <div className="text-sm text-blue-600">
              Status: <span className="font-medium">{whisperVoiceChat.status}</span>
            </div>
          </div>

          <div className="flex items-center gap-3 mb-3">
            <Button
              onClick={whisperVoiceChat.toggleListening}
              disabled={whisperVoiceChat.isProcessing}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                whisperVoiceChat.isListening
                  ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {whisperVoiceChat.isListening ? (
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-white rounded-full animate-pulse"></div>
                  Stop Listening
                </div>
              ) : whisperVoiceChat.isProcessing ? (
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Processing...
                </div>
              ) : (
                'Start Listening'
              )}
            </Button>

            {whisperVoiceChat.isProcessing && (
              <div className="text-sm text-blue-600">
                Transcribing with Whisper...
              </div>
            )}
          </div>

          {/* Transcription Display */}
          {transcription && (
            <div className="p-3 bg-green-50 rounded border border-green-200 mb-2">
              <div className="text-sm font-medium text-green-800 mb-1">✅ Last Transcription:</div>
              <div className="text-sm text-green-700">"{transcription}"</div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="p-3 bg-red-50 rounded border border-red-200 mb-2">
              <div className="text-sm font-medium text-red-800 mb-1">❌ Error:</div>
              <div className="text-xs text-red-600 mb-2">{error}</div>
              
              {/* Show specific help for microphone permission errors */}
              {error.includes('permission denied') && (
                <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200">
                  <div className="text-xs font-medium text-blue-800 mb-1">💡 How to fix:</div>
                  <div className="text-xs text-blue-700 space-y-1">
                    <div>• Click the 🔒 or camera/microphone icon in your browser's address bar</div>
                    <div>• Select "Allow" for microphone access</div>
                    <div>• Refresh the page and try again</div>
                    <div>• For Chrome: Settings → Privacy and security → Site Settings → Microphone</div>
                  </div>
                </div>
              )}
              
              {/* Show HTTPS help */}
              {error.includes('HTTPS') && (
                <div className="mt-2 p-2 bg-yellow-50 rounded border border-yellow-200">
                  <div className="text-xs font-medium text-yellow-800 mb-1">🔒 Development Setup:</div>
                  <div className="text-xs text-yellow-700 space-y-1">
                    <div>• Add NEXT_PUBLIC_BYPASS_HTTPS_CHECK=true to your .env file</div>
                    <div>• Or use localhost instead of 127.0.0.1</div>
                    <div>• Or set up HTTPS for development</div>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="text-xs text-blue-600">
            💡 Click "Start Listening" to begin voice chat. Speak clearly and the avatar will respond to your transcribed speech.
          </div>
        </div>
      )}

    </div>
  );
};