import OpenAI from 'openai';
import { NextResponse } from 'next/server';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

interface WhisperAnalysisResult {
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
  transcriptionQuality?: string;
  confidenceLevel?: string;
}

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const audioFile = formData.get('audio') as File;
    const sessionId = formData.get('sessionId') as string;

    if (!audioFile) {
      return NextResponse.json({ error: 'No audio file provided' }, { status: 400 });
    }

    if (audioFile.size === 0) {
      return NextResponse.json({ error: 'Empty audio file provided' }, { status: 400 });
    }

    // Step 1: Transcribe audio using Whisper
    const transcription = await openai.audio.transcriptions.create({
      file: audioFile,
      model: "whisper-1",
      language: "en",
    });
    
    const transcribedText = transcription.text;

    if (!transcribedText || transcribedText.trim().length === 0) {
      return NextResponse.json({
        success: false,
        error: 'No speech detected in audio'
      }, { status: 400 });
    }

    // Step 2: Enhanced pronunciation and grammar analysis with GPT-4o
    const analysisPrompt = `
You are an expert English pronunciation and grammar analyzer. Analyze the following transcribed speech and provide a detailed assessment.

TRANSCRIBED TEXT: "${transcribedText}"

ANALYSIS INSTRUCTIONS:
1. Look for signs of pronunciation issues in the transcription:
   - Unusual word substitutions that suggest mispronunciation
   - Missing or extra syllables in common words
   - Grammar patterns that indicate pronunciation confusion
   - Word choice that suggests phonetic confusion (e.g., "tree" vs "three")

2. Consider common pronunciation issues for English learners:
   - TH sounds (think, this) often transcribed as "f" or "d" sounds
   - R/L confusion in transcription
   - Vowel sound issues (bit/beat, pen/pan)
   - Consonant cluster difficulties
   - Word stress patterns affecting clarity

3. Provide realistic scores based on the quality of the transcription

Provide your analysis in the following JSON format:
{
  "pronunciationAnalysis": {
    "overallScore": 75,
    "accuracyScore": 80,
    "fluencyScore": 70,
    "completenessScore": 85,
    "commonIssues": ["specific pronunciation issues inferred from transcription"],
    "wordLevelIssues": [
      {"word": "example", "score": 60, "issue": "possible pronunciation difficulty detected"}
    ],
    "transcriptionQuality": "high/medium/low - based on clarity and coherence"
  },
  "grammarAnalysis": {
    "issues": ["specific grammar/logic issues found"]
  },
  "confidenceLevel": "high/medium/low - how confident you are in this pronunciation assessment"
}

Base your scores (0-100) on:
- Transcription clarity and coherence
- Grammar correctness indicating clear speech
- Sentence structure completeness
- Word choice appropriateness
- Logical flow suggesting natural speech patterns

Be honest about limitations - this is analysis based on text transcription, not direct audio analysis.`;

    const analysis = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        {
          role: "system",
          content: "You are an expert English language teacher specializing in pronunciation and grammar analysis. Provide detailed, constructive feedback in the requested JSON format."
        },
        {
          role: "user",
          content: analysisPrompt
        }
      ],
      max_tokens: 800,
      temperature: 0.3,
    });

    // Parse GPT-4o analysis
    let parsedAnalysis;
    try {
      const analysisContent = analysis.choices[0]?.message?.content;
      parsedAnalysis = JSON.parse(analysisContent || '{}');
    } catch (parseError) {
      console.error('Failed to parse analysis:', parseError);
      // Fallback analysis
      parsedAnalysis = {
        pronunciationAnalysis: {
          overallScore: 75,
          accuracyScore: 75,
          fluencyScore: 75,
          completenessScore: 75,
          commonIssues: [],
          wordLevelIssues: []
        },
        grammarAnalysis: {
          issues: []
        },
        confidenceLevel: "medium"
      };
    }

    // Format results to match expected interface
    const result: WhisperAnalysisResult = {
      transcribedText,
      pronunciationScore: {
        pronunciationScore: parsedAnalysis.pronunciationAnalysis?.overallScore || 75,
        accuracyScore: parsedAnalysis.pronunciationAnalysis?.accuracyScore || 75,
        fluencyScore: parsedAnalysis.pronunciationAnalysis?.fluencyScore || 75,
        completenessScore: parsedAnalysis.pronunciationAnalysis?.completenessScore || 75,
      },
      wordLevelScores: (parsedAnalysis.pronunciationAnalysis?.wordLevelIssues || []).map((item: any) => ({
        word: item.word || '',
        accuracyScore: item.score || 75,
        errorType: item.issue || undefined
      })),
      logicalIssues: parsedAnalysis.grammarAnalysis?.issues || [],
      timestamp: new Date().toISOString(),
      transcriptionQuality: parsedAnalysis.pronunciationAnalysis?.transcriptionQuality || 'medium',
      confidenceLevel: parsedAnalysis.confidenceLevel || 'medium'
    };

    return NextResponse.json({
      success: true,
      analysis: result,
      sessionId
    });

  } catch (error) {
    console.error('Whisper speech analysis error:', error);
    
    // More detailed error logging
    if (error instanceof Error) {
      console.error('Error name:', error.name);
      console.error('Error message:', error.message);
      console.error('Error stack:', error.stack);
    }
    
    return NextResponse.json({
      success: false,
      error: 'Speech analysis failed',
      details: error instanceof Error ? error.message : 'Unknown error',
      errorType: error instanceof Error ? error.name : 'UnknownError'
    }, { status: 500 });
  }
}