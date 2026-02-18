import { useCallback, useRef } from 'react';

interface SpeechAnalysisResult {
  transcribedText: string;
  pronunciationScore: {
    accuracyScore: number;
    fluencyScore: number;
    completenessScore: number;
    pronunciationScore: number;
  };
  wordLevelScores: Array<{
    word: string;
    accuracyScore: number;
    errorType?: string;
  }>;
  logicalIssues: string[];
  timestamp: string;
}

export const useSpeechAnalysis = () => {
  const currentSessionId = useRef<string | null>(null);

  const setSessionId = useCallback((sessionId: string | null) => {
    currentSessionId.current = sessionId;
  }, []);

  const analyzeAudio = useCallback(async (
    audioBlob: Blob, 
    referenceText?: string
  ): Promise<SpeechAnalysisResult | null> => {
    try {
      if (!currentSessionId.current) {
        console.warn('No active session for audio analysis');
        return null;
      }

      // Convert audio to proper format for Whisper
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      formData.append('sessionId', currentSessionId.current);

      const response = await fetch('/api/whisper-speech-analysis', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        // Store the analysis result in the session
        await fetch('/api/conversation-session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            action: 'add_azure_analysis', // Keep same action name for compatibility
            sessionId: currentSessionId.current,
            analysisData: data.analysis
          }),
        });

        return data.analysis;
      } else {
        console.error('Speech analysis failed:', data.error);
        return null;
      }
    } catch (error) {
      console.error('Error analyzing audio:', error);
      return null;
    }
  }, []);

  const getSessionPronunciationScores = useCallback(async (sessionId: string) => {
    try {
      const response = await fetch(`/api/conversation-session?sessionId=${sessionId}`);
      const data = await response.json();
      
      if (data.success && data.session) {
        const speechAnalyses = data.session.azureAnalyses || []; // Keep same property name for compatibility
        return speechAnalyses.map((analysis: SpeechAnalysisResult) => ({
          timestamp: analysis.timestamp,
          transcribedText: analysis.transcribedText,
          overallScore: analysis.pronunciationScore.pronunciationScore,
          detailedScores: analysis.pronunciationScore,
          wordScores: analysis.wordLevelScores,
          logicalIssues: analysis.logicalIssues
        }));
      }
      return [];
    } catch (error) {
      console.error('Error fetching pronunciation scores:', error);
      return [];
    }
  }, []);

  return {
    setSessionId,
    analyzeAudio,
    getSessionPronunciationScores,
  };
};