"use client";

import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';

interface ConversationAnalytics {
  sessionId?: string;
  sessionKey?: string;
  isActive: boolean;
  messageCount: number;
  startTime?: Date;
  topic: string;
}

interface ConversationMetrics {
  fluencyScore?: number;
  pronunciationScore?: number;
  engagementLevel?: string;
  vocabularyComplexity?: number;
  totalWords?: number;
  sessionDuration?: number;
}

export function ConversationAnalytics() {
  const { token } = useAuth();
  const [analytics, setAnalytics] = useState<ConversationAnalytics>({
    isActive: false,
    messageCount: 0,
    topic: 'general'
  });
  const [metrics, setMetrics] = useState<ConversationMetrics>({});

  const startSession = async (topic: string = 'general') => {
    // For now, just start a local analytics session
    // The HeyGen token creation is handled separately by the avatar component
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    setAnalytics({
      sessionId: sessionId,
      sessionKey: sessionId,
      isActive: true,
      messageCount: 0,
      startTime: new Date(),
      topic: topic
    });

    // Optionally, try to register with Flask backend (non-blocking)
    if (token) {
      try {
        const response = await fetch('/api/conversation/start-session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ topic }),
        });
        
        if (response.ok) {
          await response.json();
        }
      } catch (error) {
        // Backend session registration failed (non-critical)
      }
    }
    
    return { success: true, sessionId, topic };
  };

  const trackMessage = async (message: string) => {
    if (!analytics.sessionKey || !token) return;

    try {
      const response = await fetch('/api/conversation/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          sessionKey: analytics.sessionKey,
          message: message
        }),
      });

      const data = await response.json();

      if (data.success) {
        setAnalytics(prev => ({
          ...prev,
          messageCount: prev.messageCount + 1
        }));

        // Update metrics if provided
        if (data.conversationAnalysis) {
          setMetrics(prev => ({
            ...prev,
            totalWords: (prev.totalWords || 0) + (data.conversationAnalysis.word_count || 0),
            engagementLevel: data.conversationAnalysis.engagement_level
          }));
        }

        if (data.pronunciationScore) {
          setMetrics(prev => ({
            ...prev,
            pronunciationScore: data.pronunciationScore
          }));
        }

      }
    } catch (error) {
      console.error('Error tracking message:', error);
    }
  };

  const endSession = async () => {
    if (!analytics.sessionKey || !token) return;

    try {
      const response = await fetch('/api/conversation/end-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          sessionKey: analytics.sessionKey
        }),
      });

      const data = await response.json();

      if (data.success && data.analytics) {
        setMetrics({
          fluencyScore: data.analytics.fluency_score,
          pronunciationScore: data.analytics.pronunciation_score,
          engagementLevel: data.analytics.engagement_level,
          vocabularyComplexity: data.analytics.vocabulary_complexity_score,
          totalWords: data.analytics.total_words_spoken,
          sessionDuration: data.analytics.session_duration_minutes
        });

        return data.analytics;
      }
    } catch (error) {
      console.error('Error ending session:', error);
    } finally {
      setAnalytics({
        isActive: false,
        messageCount: 0,
        topic: 'general'
      });
    }
  };

  const getDuration = () => {
    if (!analytics.startTime) return 0;
    return Math.floor((new Date().getTime() - analytics.startTime.getTime()) / 1000 / 60);
  };

  return {
    analytics,
    metrics,
    startSession,
    trackMessage,
    endSession,
    getDuration
  };
}

// Analytics display component
export function AnalyticsDisplay({ analytics, metrics }: { 
  analytics: ConversationAnalytics, 
  metrics: ConversationMetrics 
}) {
  if (!analytics.isActive && Object.keys(metrics).length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg p-4 border border-gray-200 mt-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-3">
        📊 Conversation Analytics
      </h3>
      
      {analytics.isActive && (
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{analytics.messageCount}</div>
            <div className="text-sm text-gray-600">Messages</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{analytics.topic}</div>
            <div className="text-sm text-gray-600">Topic</div>
          </div>
        </div>
      )}

      {Object.keys(metrics).length > 0 && (
        <div className="grid grid-cols-2 gap-4">
          {metrics.fluencyScore && (
            <div className="text-center">
              <div className="text-xl font-bold text-purple-600">{metrics.fluencyScore}/100</div>
              <div className="text-sm text-gray-600">Fluency</div>
            </div>
          )}
          {metrics.pronunciationScore && (
            <div className="text-center">
              <div className="text-xl font-bold text-orange-600">{metrics.pronunciationScore}/100</div>
              <div className="text-sm text-gray-600">Pronunciation</div>
            </div>
          )}
          {metrics.totalWords && (
            <div className="text-center">
              <div className="text-xl font-bold text-indigo-600">{metrics.totalWords}</div>
              <div className="text-sm text-gray-600">Words Spoken</div>
            </div>
          )}
          {metrics.sessionDuration && (
            <div className="text-center">
              <div className="text-xl font-bold text-teal-600">{metrics.sessionDuration}m</div>
              <div className="text-sm text-gray-600">Duration</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}