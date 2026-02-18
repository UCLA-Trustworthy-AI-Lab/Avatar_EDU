import OpenAI from 'openai';
import { NextResponse } from 'next/server';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const audioFile = formData.get('audio') as File;

    if (!audioFile) {
      return NextResponse.json({ 
        success: false, 
        error: 'No audio file provided' 
      });
    }

    if (audioFile.size === 0) {
      return NextResponse.json({ 
        success: false, 
        error: 'Empty audio file' 
      });
    }

    try {
      const transcription = await openai.audio.transcriptions.create({
        file: audioFile,
        model: "whisper-1",
        language: "en",
      });
      
      return NextResponse.json({
        success: true,
        transcription: transcription.text,
        audioSize: audioFile.size,
        audioType: audioFile.type
      });
      
    } catch (whisperError) {
      console.error('Whisper API error:', whisperError);
      
      return NextResponse.json({
        success: false,
        error: 'Whisper API failed',
        details: whisperError instanceof Error ? whisperError.message : 'Unknown Whisper error',
        audioSize: audioFile.size,
        audioType: audioFile.type
      });
    }

  } catch (error) {
    console.error('Test API error:', error);
    return NextResponse.json({
      success: false,
      error: 'Test API failed',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}