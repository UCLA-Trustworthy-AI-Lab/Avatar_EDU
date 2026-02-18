import OpenAI from 'openai';
import { NextResponse } from 'next/server';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

interface AnalysisResult {
  pronunciationIssues: string[];
  logicalIssues: string[];
  timestamp: string;
  originalText: string;
}

export async function POST(request: Request) {
  try {
    const { userMessage, sessionId } = await request.json();

    // Analyze pronunciation and logical issues separately from conversation
    const analysisCompletion = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        {
          role: "system",
          content: `You are an English language analyzer. Analyze the student's speech for:

          1. PRONUNCIATION ISSUES: Common pronunciation mistakes that English learners make
          2. LOGICAL/GRAMMAR ISSUES: Grammar, sentence structure, word choice problems

          Return a JSON object with this structure:
          {
            "pronunciationIssues": ["specific pronunciation errors found"],
            "logicalIssues": ["specific grammar/logic errors found"]
          }

          Be specific about what was incorrect. If no issues found, return empty arrays.
          Only analyze actual errors - don't make assumptions about pronunciation from text alone unless there are clear spelling/phonetic indicators.`
        },
        {
          role: "user",
          content: `Analyze this student speech: "${userMessage}"`
        }
      ],
      max_tokens: 300,
      temperature: 0.3,
    });

    const analysisContent = analysisCompletion.choices[0]?.message?.content;
    let analysis: AnalysisResult;

    try {
      const parsedAnalysis = JSON.parse(analysisContent || '{}');
      analysis = {
        pronunciationIssues: parsedAnalysis.pronunciationIssues || [],
        logicalIssues: parsedAnalysis.logicalIssues || [],
        timestamp: new Date().toISOString(),
        originalText: userMessage
      };
    } catch (parseError) {
      // Fallback if JSON parsing fails
      analysis = {
        pronunciationIssues: [],
        logicalIssues: [],
        timestamp: new Date().toISOString(),
        originalText: userMessage
      };
    }

    return NextResponse.json({ 
      success: true,
      analysis,
      sessionId 
    });
  } catch (error) {
    console.error('Conversation analysis error:', error);
    return NextResponse.json({ 
      success: false,
      error: 'Analysis failed',
      analysis: {
        pronunciationIssues: [],
        logicalIssues: [],
        timestamp: new Date().toISOString(),
        originalText: ''
      }
    }, { status: 500 });
  }
}