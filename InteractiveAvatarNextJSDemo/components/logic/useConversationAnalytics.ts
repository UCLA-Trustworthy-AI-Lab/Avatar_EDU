import { useCallback, useMemo } from 'react';
import { useMessageHistory } from './useMessageHistory';
import { MessageSender } from './context';

interface ConversationAnalytics {
  totalMessages: number;
  userMessages: number;
  avatarMessages: number;
  averageMessageLength: number;
  conversationDuration: string;
  messageHistory: Array<{
    sender: 'user' | 'avatar';
    content: string;
    timestamp: string;
    id: string;
  }>;
}

interface VoiceAnalysisData {
  transcribedText: string;
  pronunciationScore?: number;
  analysisData?: any;
  timestamp: string;
}

// Store voice analysis data separately (in-memory for now)
const voiceAnalysisStore = new Map<string, VoiceAnalysisData>();

export const useConversationAnalytics = () => {
  const { messages } = useMessageHistory();

  // Convert message history to analytics format
  const conversationAnalytics: ConversationAnalytics = useMemo(() => {
    const userMessages = messages.filter(m => m.sender === MessageSender.CLIENT);
    const avatarMessages = messages.filter(m => m.sender === MessageSender.AVATAR);
    
    const totalLength = messages.reduce((sum, m) => sum + m.content.length, 0);
    const averageLength = messages.length > 0 ? Math.round(totalLength / messages.length) : 0;

    return {
      totalMessages: messages.length,
      userMessages: userMessages.length,
      avatarMessages: avatarMessages.length,
      averageMessageLength: averageLength,
      conversationDuration: 'Current session', // Could calculate based on timestamps
      messageHistory: messages.map(m => ({
        sender: m.sender === MessageSender.CLIENT ? 'user' as const : 'avatar' as const,
        content: m.content,
        timestamp: new Date().toISOString(), // Messages don't have timestamps, using current time
        id: m.id
      }))
    };
  }, [messages]);

  // Store voice analysis data linked to message ID
  const addVoiceAnalysis = useCallback((messageId: string, analysisData: VoiceAnalysisData) => {
    voiceAnalysisStore.set(messageId, analysisData);
  }, []);

  // Get voice analysis for a specific message
  const getVoiceAnalysis = useCallback((messageId: string): VoiceAnalysisData | null => {
    return voiceAnalysisStore.get(messageId) || null;
  }, []);

  // Get all voice analyses
  const getAllVoiceAnalyses = useCallback((): VoiceAnalysisData[] => {
    return Array.from(voiceAnalysisStore.values());
  }, []);

  // Generate conversation report
  const generateConversationReport = useCallback(() => {
    const voiceAnalyses = getAllVoiceAnalyses();
    const userMessages = conversationAnalytics.messageHistory.filter(m => m.sender === 'user');
    
    // Calculate pronunciation scores
    const pronunciationScores = voiceAnalyses
      .filter(v => v.pronunciationScore !== undefined)
      .map(v => v.pronunciationScore!);
    
    const avgPronunciation = pronunciationScores.length > 0 
      ? Math.round(pronunciationScores.reduce((sum, score) => sum + score, 0) / pronunciationScores.length)
      : 0;

    return {
      sessionInfo: {
        sessionId: `session_${Date.now()}`,
        startTime: new Date().toISOString(),
        endTime: new Date().toISOString(),
        duration: `${conversationAnalytics.totalMessages} messages exchanged`
      },
      conversationStats: {
        totalMessages: conversationAnalytics.totalMessages,
        userMessages: conversationAnalytics.userMessages,
        avatarMessages: conversationAnalytics.avatarMessages,
        averageMessageLength: conversationAnalytics.averageMessageLength
      },
      pronunciationSummary: {
        totalAudioAnalyses: voiceAnalyses.length,
        azureOverallScore: avgPronunciation,
        totalIssues: 0, // Could analyze for issues
        issues: [] // Could extract from analysis data
      },
      logicalSummary: {
        totalIssues: 0,
        issues: []
      },
      messageHistory: conversationAnalytics.messageHistory,
      voiceAnalyses: voiceAnalyses,
      detailedAnalysis: [] // Legacy compatibility
    };
  }, [conversationAnalytics, getAllVoiceAnalyses]);

  // Clear all data (for new conversation)
  const clearAnalytics = useCallback(() => {
    voiceAnalysisStore.clear();
  }, []);

  return {
    conversationAnalytics,
    addVoiceAnalysis,
    getVoiceAnalysis,
    getAllVoiceAnalyses,
    generateConversationReport,
    clearAnalytics,
    
    // Computed values
    hasMessages: messages.length > 0,
    hasVoiceData: voiceAnalysisStore.size > 0,
  };
};