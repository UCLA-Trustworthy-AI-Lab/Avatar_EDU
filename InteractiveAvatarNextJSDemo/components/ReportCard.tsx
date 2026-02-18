'use client';

import { useState } from 'react';
import { Button } from './Button';
import { useConversationAnalytics } from './logic/useConversationAnalytics';

// Simple Card components to replace UI library
const Card = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={`bg-white rounded-lg shadow-lg ${className || ''}`}>
    {children}
  </div>
);

const CardHeader = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={`p-6 border-b ${className || ''}`}>
    {children}
  </div>
);

const CardTitle = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <h2 className={`text-xl font-semibold ${className || ''}`}>
    {children}
  </h2>
);

const CardContent = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={`p-6 ${className || ''}`}>
    {children}
  </div>
);

interface ReportData {
  sessionInfo: {
    sessionId: string;
    startTime: string;
    endTime?: string;
    duration: string;
  };
  conversationStats: {
    totalMessages: number;
    userMessages: number;
    avatarMessages: number;
    averageMessageLength: number;
  };
  pronunciationSummary: {
    totalIssues: number;
    issues: string[];
    azureOverallScore: number;
    totalAudioAnalyses: number;
  };
  logicalSummary: {
    totalIssues: number;
    issues: string[];
  };
  messageHistory: Array<{
    sender: 'user' | 'avatar';
    content: string;
    timestamp: string;
    id: string;
  }>;
  voiceAnalyses: Array<{
    transcribedText: string;
    pronunciationScore?: number;
    analysisData?: any;
    timestamp: string;
  }>;
  detailedAnalysis: Array<{
    pronunciationIssues: string[];
    logicalIssues: string[];
    timestamp: string;
    originalText: string;
  }>;
}

interface ReportCardProps {
  onClose: () => void;
}

export default function ReportCard({ onClose }: ReportCardProps) {
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { generateConversationReport, hasMessages, hasVoiceData } = useConversationAnalytics();

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Use the conversation analytics instead of API calls
      const report = generateConversationReport();
      setReportData(report);
    } catch (err) {
      setError('Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleString();
  };

  if (!hasMessages) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>No Conversation Data</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Start chatting with the avatar to generate a conversation report.</p>
          <div className="mt-2 text-sm text-gray-600">
            {hasVoiceData ? "Voice data available, but no chat messages found." : "No voice or chat data available yet."}
          </div>
          <Button onClick={onClose} className="mt-4">Close</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>English Conversation Report Card</CardTitle>
        <Button onClick={onClose} className="bg-gray-500 hover:bg-gray-600">Close</Button>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {!reportData && !loading && (
          <div className="text-center">
            <Button onClick={fetchReport}>Generate Report</Button>
          </div>
        )}
        
        {loading && (
          <div className="text-center">
            <p>Generating your report...</p>
          </div>
        )}
        
        {error && (
          <div className="text-center text-red-500">
            <p>Error: {error}</p>
            <Button onClick={fetchReport} className="mt-2">Try Again</Button>
          </div>
        )}
        
        {reportData && (
          <div className="space-y-6">
            {/* Part 1: Session Information */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Part 1: Session Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="font-medium">Start Time:</p>
                    <p className="text-sm text-gray-600">{formatDate(reportData.sessionInfo.startTime)}</p>
                  </div>
                  {reportData.sessionInfo.endTime && (
                    <div>
                      <p className="font-medium">End Time:</p>
                      <p className="text-sm text-gray-600">{formatDate(reportData.sessionInfo.endTime)}</p>
                    </div>
                  )}
                  <div>
                    <p className="font-medium">Duration:</p>
                    <p className="text-sm text-gray-600">{reportData.sessionInfo.duration}</p>
                  </div>
                  <div>
                    <p className="font-medium">Session ID:</p>
                    <p className="text-sm text-gray-600 font-mono">{reportData.sessionInfo.sessionId}</p>
                  </div>
                </div>
                
                {/* Conversation Statistics */}
                <div className="border-t pt-4">
                  <p className="font-medium mb-3">Conversation Statistics</p>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Total Messages:</p>
                      <p className="text-lg font-semibold text-blue-600">{reportData.conversationStats.totalMessages}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Student Messages:</p>
                      <p className="text-lg font-semibold text-green-600">{reportData.conversationStats.userMessages}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Teacher Responses:</p>
                      <p className="text-lg font-semibold text-purple-600">{reportData.conversationStats.avatarMessages}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Avg Message Length:</p>
                      <p className="text-lg font-semibold text-orange-600">{reportData.conversationStats.averageMessageLength} chars</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Part 2: Pronunciation Analysis */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Part 2: Pronunciation Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-6 mb-6">
                  <div>
                    <p className="font-medium text-lg">AI Speech Analysis</p>
                    <div className="mt-3">
                      <p className="text-sm text-gray-600">Audio Recordings Analyzed: {reportData.pronunciationSummary.totalAudioAnalyses}</p>
                      <div className="mt-2">
                        <p className="text-sm font-medium">Overall Pronunciation Score:</p>
                        <div className="flex items-center gap-2 mt-1">
                          <div className="text-2xl font-bold text-blue-600">
                            {reportData.pronunciationSummary.azureOverallScore}/100
                          </div>
                          <div className={`px-2 py-1 rounded text-xs font-medium ${
                            reportData.pronunciationSummary.azureOverallScore >= 80 ? 'bg-green-100 text-green-800' :
                            reportData.pronunciationSummary.azureOverallScore >= 60 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {reportData.pronunciationSummary.azureOverallScore >= 80 ? 'Excellent' :
                             reportData.pronunciationSummary.azureOverallScore >= 60 ? 'Good' : 'Needs Practice'}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div>
                    <p className="font-medium text-lg">Text-Based Issues</p>
                    <div className="mt-3">
                      <p className="text-sm text-gray-600">Total Issues Found: {reportData.pronunciationSummary.totalIssues}</p>
                      {reportData.pronunciationSummary.issues.length > 0 ? (
                        <ul className="list-disc list-inside space-y-1 mt-2">
                          {reportData.pronunciationSummary.issues.slice(0, 3).map((issue, index) => (
                            <li key={index} className="text-sm">{issue}</li>
                          ))}
                          {reportData.pronunciationSummary.issues.length > 3 && (
                            <li className="text-sm text-gray-500">+ {reportData.pronunciationSummary.issues.length - 3} more...</li>
                          )}
                        </ul>
                      ) : (
                        <p className="text-green-600 text-sm mt-2">No text-based pronunciation issues detected!</p>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Voice Analysis Data */}
                {reportData.voiceAnalyses && reportData.voiceAnalyses.length > 0 && (
                  <div className="border-t pt-4">
                    <p className="font-medium mb-3">Voice Transcriptions ({reportData.voiceAnalyses.length})</p>
                    <div className="space-y-3 max-h-64 overflow-y-auto">
                      {reportData.voiceAnalyses.map((analysis, index) => (
                        <div key={index} className="bg-gray-50 p-3 rounded">
                          <div className="flex justify-between items-start mb-2">
                            <p className="text-sm font-medium">"{analysis.transcribedText}"</p>
                            <span className="text-xs text-gray-500">{formatDate(analysis.timestamp)}</span>
                          </div>
                          {analysis.pronunciationScore && (
                            <div className="text-xs text-blue-600">
                              <span className="text-gray-600">Score:</span>
                              <span className="font-medium ml-1">{analysis.pronunciationScore}/100</span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Part 3: Logical/Grammar Issues */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Part 3: Grammar & Logic Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <p className="font-medium">Total Issues Found: {reportData.logicalSummary.totalIssues}</p>
                </div>
                {reportData.logicalSummary.issues.length > 0 ? (
                  <ul className="list-disc list-inside space-y-1">
                    {reportData.logicalSummary.issues.map((issue, index) => (
                      <li key={index} className="text-sm">{issue}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-green-600">No grammar or logic issues detected!</p>
                )}
              </CardContent>
            </Card>

            {/* Conversation Timeline */}
            {reportData.messageHistory.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Conversation Timeline</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {reportData.messageHistory.map((message, index) => (
                      <div key={index} className={`border-l-4 pl-4 ${
                        message.sender === 'user' ? 'border-blue-200' : 'border-green-200'
                      }`}>
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-xs px-2 py-1 rounded ${
                            message.sender === 'user' 
                              ? 'bg-blue-100 text-blue-800' 
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {message.sender === 'user' ? '👤 Student' : '🤖 Teacher'}
                          </span>
                          <p className="text-xs text-gray-500">{formatDate(message.timestamp)}</p>
                        </div>
                        <p className="text-sm">"{message.content}"</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}