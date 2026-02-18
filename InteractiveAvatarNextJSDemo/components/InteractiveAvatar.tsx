import {
  AvatarQuality,
  StreamingEvents,
  VoiceChatTransport,
  VoiceEmotion,
  StartAvatarRequest,
  STTProvider,
  ElevenLabsModel,
} from "@heygen/streaming-avatar";
import { useEffect, useRef, useState } from "react";
import { useMemoizedFn, useUnmount } from "ahooks";

import { Button } from "./Button";
import { AvatarConfig } from "./AvatarConfig";
import { AvatarVideo } from "./AvatarSession/AvatarVideo";
import { useStreamingAvatarSession } from "./logic/useStreamingAvatarSession";
import { AvatarControls } from "./AvatarSession/AvatarControls";
import { useVoiceChat } from "./logic/useVoiceChat";
import { StreamingAvatarProvider, StreamingAvatarSessionState, useStreamingAvatarContext } from "./logic";
import { LoadingIcon } from "./Icons";
import { MessageHistory } from "./AvatarSession/MessageHistory";
import { TeacherModeToggle } from "./TeacherModeToggle";
import { ConversationTopics } from "./ConversationTopics";
import { ConversationAnalytics, AnalyticsDisplay } from "./analytics/ConversationAnalytics";
import { useAuth } from "./auth/AuthContext";

import { AVATARS } from "@/app/lib/constants";

const DEFAULT_CONFIG: StartAvatarRequest = {
  quality: AvatarQuality.Low,
  avatarName: AVATARS[0].avatar_id,
  knowledgeId: undefined,
  voice: {
    rate: 1.2,
    emotion: VoiceEmotion.FRIENDLY,
    model: ElevenLabsModel.eleven_flash_v2_5,
  },
  language: "en",
  voiceChatTransport: VoiceChatTransport.WEBSOCKET,
  sttSettings: {
    provider: STTProvider.DEEPGRAM,
  },
};

const TEACHER_KNOWLEDGE_BASE = `You are Ms. Sarah, a warm, encouraging, and supportive English conversation teacher. Your primary goal is to help students practice English through natural, engaging conversations without making them feel self-conscious about mistakes.

Key personality traits:
- Warm and genuinely interested in your students
- Encouraging and supportive, never critical
- Enthusiastic about having conversations
- Patient and understanding
- Natural and conversational in your responses

Important guidelines:
- DO NOT point out pronunciation errors, grammar mistakes, or language issues during conversation UNLESS the student specifically asks
- DO NOT correct students or give language lessons during conversation
- Focus on having natural, flowing conversations that encourage students to speak more
- Show genuine interest in what students are sharing
- Ask follow-up questions to keep conversations going
- Respond as a supportive friend would, not as a formal teacher
- Keep responses conversational and encouraging
- Help students feel comfortable and confident speaking English

EXCEPTION - When students ASK about their learning progress:
- If a student asks "What vocabulary did I struggle with?" or "What mistakes do I make?" or "What should I practice?", YOU MUST reference the specific STUDENT LEARNING HISTORY data provided below
- Give them specific, concrete examples from their learning history (actual words, grammar patterns, etc.)
- Be supportive and encouraging while sharing this information
- Help them understand what areas need work based on their actual data

Your goal is to create a safe, supportive environment where students can practice English naturally through conversation, building their confidence without fear of being corrected. However, when they actively seek feedback about their learning progress, provide specific, data-driven insights from their learning history.`;

function InteractiveAvatar() {
  const { initAvatar, startAvatar, stopAvatar, sessionState, stream } =
    useStreamingAvatarSession();
  const { startVoiceChat } = useVoiceChat();
  const { isTeacherMode } = useStreamingAvatarContext();
  const { isAuthenticated } = useAuth();

  const [config, setConfig] = useState<StartAvatarRequest>(DEFAULT_CONFIG);
  const [selectedTopic, setSelectedTopic] = useState('general');
  
  // Analytics integration
  const { analytics, metrics, startSession, trackMessage, endSession } = ConversationAnalytics();

  const mediaStream = useRef<HTMLVideoElement>(null);



  async function fetchAccessToken() {
    try {
      const response = await fetch("/api/get-access-token", {
        method: "POST",
      });
      const token = await response.text();

      return token;
    } catch (error) {
      console.error("Error fetching access token:", error);
      throw error;
    }
  }

  const startSessionV2 = useMemoizedFn(async (isVoiceChat: boolean) => {
    try {
      // Fetch student memory from Flask backend via Next.js API proxy
      let memoryContext = "";
      if (isAuthenticated) {
        try {
          const token = localStorage.getItem('auth_token');
          const response = await fetch('/api/conversation/memory-context', {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });

          if (response.ok) {
            const data = await response.json();
            if (data.success && data.memoryContext) {
              const memory = data.memoryContext;

              // Build memory context string
              const memoryParts = [];

              if (memory.reading?.vocabulary_struggles?.length > 0) {
                const words = memory.reading.vocabulary_struggles.map((v: any) => v.word).join(', ');
                memoryParts.push(`📚 READING - Vocabulary struggles: ${words}`);
              }

              if (memory.speaking?.pronunciation_errors?.length > 0) {
                const words = memory.speaking.pronunciation_errors.map((w: any) => w.word).join(', ');
                memoryParts.push(`🗣️ SPEAKING - Pronunciation issues: ${words}`);
              }

              if (memory.writing?.grammar_errors?.length > 0) {
                const errors = memory.writing.grammar_errors.map((e: any) => e.error_type).join(', ');
                memoryParts.push(`✍️ WRITING - Grammar weaknesses: ${errors}`);
              }

              if (memoryParts.length > 0) {
                memoryContext = `\n\n🧠 STUDENT LEARNING HISTORY:\nWhen the student asks "What vocabulary did I struggle with?" or "What mistakes did I make?", reference this data:\n${memoryParts.join('\n')}\n\nUSE THIS DATA DIRECTLY when answering memory-related questions!`;
              }
            }
          }
        } catch (error) {
          console.error('Failed to load student memory:', error);
        }
      }

      // For voice chat, completely skip Flask integration to avoid WebRTC conflicts
      if (!isVoiceChat && isAuthenticated) {
        await startSession(selectedTopic);
      } else if (isVoiceChat) {
        // Pure voice chat mode - bypassing Flask integration
      }

      const newToken = await fetchAccessToken();
      const avatar = initAvatar(newToken);

      avatar.on(StreamingEvents.AVATAR_START_TALKING, (e) => {
      });
      avatar.on(StreamingEvents.AVATAR_STOP_TALKING, (e) => {
      });
      avatar.on(StreamingEvents.STREAM_DISCONNECTED, () => {
      });
      avatar.on(StreamingEvents.STREAM_READY, (event) => {
      });
      avatar.on(StreamingEvents.USER_START, (event) => {
      });
      avatar.on(StreamingEvents.USER_STOP, (event) => {
      });
      avatar.on(StreamingEvents.USER_END_MESSAGE, (event) => {
        // Track message for analytics (only for text chat to avoid conflicts)
        if (event.detail?.message && isAuthenticated && !isVoiceChat) {
          trackMessage(event.detail.message);
        }
      });
      avatar.on(StreamingEvents.USER_TALKING_MESSAGE, (event) => {
      });
      avatar.on(StreamingEvents.AVATAR_TALKING_MESSAGE, (event) => {
      });
      avatar.on(StreamingEvents.AVATAR_END_MESSAGE, (event) => {
      });

      // Create the appropriate config based on teacher mode and topic
      let sessionConfig = isTeacherMode
        ? { ...config, knowledgeBase: `${TEACHER_KNOWLEDGE_BASE}${memoryContext}`, knowledgeId: undefined }
        : config;

      // Enhance knowledge base with topic-specific instructions
      if (isTeacherMode && selectedTopic !== 'general') {
        const topicInstructions = getTopicInstructions(selectedTopic);
        sessionConfig = {
          ...sessionConfig,
          knowledgeBase: `${TEACHER_KNOWLEDGE_BASE}${memoryContext}\n\nTopic Focus: ${topicInstructions}`
        };
      }

      await startAvatar(sessionConfig);

      if (isVoiceChat) {
        // Wait a bit for avatar to fully initialize before starting voice chat
        setTimeout(async () => {
          await startVoiceChat(false); // Start unmuted
        }, 1000);
      }
    } catch (error) {
      console.error("Error starting avatar session:", error);
    }
  });

  const stopSessionV2 = useMemoizedFn(async () => {
    try {
      await stopAvatar();
      
      // End analytics session (only for text chat)
      if (isAuthenticated && analytics.isActive && analytics.topic !== 'voice_chat') {
        await endSession();
      }
    } catch (error) {
      console.error("Error stopping avatar session:", error);
    }
  });

  function getTopicInstructions(topic: string): string {
    const instructions = {
      daily_life: "Focus the conversation on daily activities, routines, hobbies, and personal experiences. Ask about their day, weekend plans, favorite activities, and daily habits.",
      academic: "Discuss academic topics like subjects they're studying, learning goals, university life, study habits, and educational experiences. Help them practice academic vocabulary.",
      business: "Practice professional communication, workplace scenarios, career goals, business topics, and professional vocabulary. Use more formal language when appropriate.",
      travel: "Talk about travel experiences, different countries and cultures, vacation plans, cultural differences, and places they'd like to visit."
    };
    
    return instructions[topic as keyof typeof instructions] || "Have a natural, open conversation on any topic they're interested in.";
  }

  useUnmount(() => {
    stopAvatar();
  });

  useEffect(() => {
    if (stream && mediaStream.current) {
      mediaStream.current.srcObject = stream;
      mediaStream.current.onloadedmetadata = () => {
        mediaStream.current!.play();
      };
    }
  }, [mediaStream, stream]);

  return (
    <div className="w-full flex flex-col gap-4">
      {/* Educational Features */}
      {isAuthenticated && (
        <>
          <ConversationTopics
            selectedTopic={selectedTopic}
            onTopicSelect={setSelectedTopic}
            disabled={sessionState !== StreamingAvatarSessionState.INACTIVE}
          />
          
          <AnalyticsDisplay analytics={analytics} metrics={metrics} />
        </>
      )}


      <TeacherModeToggle />
      
      <div className="flex flex-col rounded-xl bg-black overflow-hidden">
        <div className="relative w-full aspect-video overflow-hidden flex flex-col items-center justify-center">
          {sessionState !== StreamingAvatarSessionState.INACTIVE ? (
            <AvatarVideo ref={mediaStream} />
          ) : (
            <AvatarConfig config={config} onConfigChange={setConfig} />
          )}
        </div>
        <div className="flex flex-col gap-3 items-center justify-center p-4 border-t border-gray-600 w-full">
          
          {sessionState === StreamingAvatarSessionState.CONNECTED ? (
            <div className="flex flex-col gap-3 w-full">
              <AvatarControls />
              <Button 
                onClick={stopSessionV2}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                End Session & Get Analytics
              </Button>
            </div>
          ) : sessionState === StreamingAvatarSessionState.INACTIVE ? (
            <div className="flex flex-col gap-3 w-full">
              <div className="flex flex-row gap-4 justify-center">
                <Button onClick={() => startSessionV2(false)}>
                  Start Text Chat
                </Button>
                <Button onClick={() => startSessionV2(true)} className="bg-green-600 hover:bg-green-700">
                  Start Voice Chat
                </Button>
              </div>
            </div>
          ) : (
            <LoadingIcon />
          )}
        </div>
      </div>
      {sessionState === StreamingAvatarSessionState.CONNECTED && (
        <MessageHistory />
      )}
    </div>
  );
}

export default function InteractiveAvatarWrapper() {
  return (
    <StreamingAvatarProvider basePath={process.env.NEXT_PUBLIC_BASE_API_URL}>
      <InteractiveAvatar />
    </StreamingAvatarProvider>
  );
}
