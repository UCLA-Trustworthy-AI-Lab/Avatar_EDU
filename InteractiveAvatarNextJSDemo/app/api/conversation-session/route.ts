import { NextResponse } from 'next/server';

interface ConversationSession {
  sessionId: string;
  startTime: string;
  endTime?: string;
  analysisData: Array<{
    pronunciationIssues: string[];
    logicalIssues: string[];
    timestamp: string;
    originalText: string;
  }>;
  azureAnalyses: Array<{
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
  }>;
}

// In-memory storage for demo (in production, use a database)
const sessions = new Map<string, ConversationSession>();

export async function POST(request: Request) {
  try {
    const { action, sessionId, analysisData } = await request.json();

    switch (action) {
      case 'start':
        const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const newSession: ConversationSession = {
          sessionId: newSessionId,
          startTime: new Date().toISOString(),
          analysisData: [],
          azureAnalyses: []
        };
        sessions.set(newSessionId, newSession);
        return NextResponse.json({ success: true, sessionId: newSessionId });

      case 'add_analysis':
        if (!sessionId || !sessions.has(sessionId)) {
          return NextResponse.json({ success: false, error: 'Invalid session ID' }, { status: 400 });
        }
        const session = sessions.get(sessionId)!;
        session.analysisData.push(analysisData);
        sessions.set(sessionId, session);
        return NextResponse.json({ success: true });

      case 'add_azure_analysis':
        if (!sessionId || !sessions.has(sessionId)) {
          return NextResponse.json({ success: false, error: 'Invalid session ID' }, { status: 400 });
        }
        const azureSession = sessions.get(sessionId)!;
        azureSession.azureAnalyses.push(analysisData);
        sessions.set(sessionId, azureSession);
        return NextResponse.json({ success: true });

      case 'end':
        if (!sessionId || !sessions.has(sessionId)) {
          return NextResponse.json({ success: false, error: 'Invalid session ID' }, { status: 400 });
        }
        const endingSession = sessions.get(sessionId)!;
        endingSession.endTime = new Date().toISOString();
        sessions.set(sessionId, endingSession);
        return NextResponse.json({ success: true });

      case 'get_report':
        if (!sessionId || !sessions.has(sessionId)) {
          return NextResponse.json({ success: false, error: 'Session not found' }, { status: 404 });
        }
        const reportSession = sessions.get(sessionId)!;
        
        // Generate report summary
        const allPronunciationIssues = reportSession.analysisData.flatMap(d => d.pronunciationIssues);
        const allLogicalIssues = reportSession.analysisData.flatMap(d => d.logicalIssues);
        
        // Azure analysis summary
        const azureLogicalIssues = reportSession.azureAnalyses.flatMap(d => d.logicalIssues);
        const avgPronunciationScore = reportSession.azureAnalyses.length > 0 
          ? reportSession.azureAnalyses.reduce((sum, a) => sum + a.pronunciationScore.pronunciationScore, 0) / reportSession.azureAnalyses.length
          : 0;
        
        const report = {
          sessionInfo: {
            sessionId: reportSession.sessionId,
            startTime: reportSession.startTime,
            endTime: reportSession.endTime,
            duration: reportSession.endTime ? 
              Math.round((new Date(reportSession.endTime).getTime() - new Date(reportSession.startTime).getTime()) / 1000 / 60) + ' minutes' 
              : 'Ongoing'
          },
          pronunciationSummary: {
            totalIssues: allPronunciationIssues.length,
            issues: allPronunciationIssues,
            azureOverallScore: Math.round(avgPronunciationScore),
            totalAudioAnalyses: reportSession.azureAnalyses.length
          },
          logicalSummary: {
            totalIssues: allLogicalIssues.length + azureLogicalIssues.length,
            issues: [...allLogicalIssues, ...azureLogicalIssues]
          },
          detailedAnalysis: reportSession.analysisData,
          azureAnalyses: reportSession.azureAnalyses
        };
        
        return NextResponse.json({ success: true, report });

      default:
        return NextResponse.json({ success: false, error: 'Invalid action' }, { status: 400 });
    }
  } catch (error) {
    console.error('Session management error:', error);
    return NextResponse.json({ success: false, error: 'Server error' }, { status: 500 });
  }
}

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const sessionId = url.searchParams.get('sessionId');
    
    if (!sessionId || !sessions.has(sessionId)) {
      return NextResponse.json({ success: false, error: 'Session not found' }, { status: 404 });
    }
    
    const session = sessions.get(sessionId)!;
    return NextResponse.json({ success: true, session });
  } catch (error) {
    console.error('Session retrieval error:', error);
    return NextResponse.json({ success: false, error: 'Server error' }, { status: 500 });
  }
}