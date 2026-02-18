import OpenAI from 'openai';
import { NextResponse } from 'next/server';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(request: Request) {
  try {
    const { userMessage, authToken } = await request.json();

    // Analyze user engagement level
    const isShortResponse = userMessage.trim().split(' ').length <= 3;
    const isUnclearOrVague = /^(yes|no|ok|okay|fine|good|bad|maybe|i don't know|idk)$/i.test(userMessage.trim());
    const needsMoreEngagement = isShortResponse || isUnclearOrVague;

    // Create conversation starters for when students need more engagement
    const conversationStarters = [
      "What's the most interesting place you've ever visited? I'd love to hear about it!",
      "If you could have dinner with anyone in the world, who would it be and why?",
      "What's something you've learned recently that really surprised you?",
      "Tell me about a hobby or activity that makes you lose track of time.",
      "What's your favorite season and what do you love most about it?",
      "If you could travel anywhere tomorrow, where would you go?",
      "What's the best advice someone has ever given you?",
      "What kind of music do you enjoy? Do you have a favorite song right now?",
      "What's something you're really looking forward to?",
      "Tell me about a tradition your family or culture has that you really enjoy."
    ];

    const randomStarter = conversationStarters[Math.floor(Math.random() * conversationStarters.length)];

    // Load student's learning memory from Flask backend
    const flaskApiUrl = process.env.NEXT_PUBLIC_FLASK_API_URL || 'http://localhost:5001';
    let memoryContext = '';
    if (authToken) {
      try {
        const memoryResponse = await fetch(`${flaskApiUrl}/api/conversation/memory-context`, {
          headers: {
            'Authorization': `Bearer ${authToken}`
          }
        });

        if (memoryResponse.ok) {
          const memoryData = await memoryResponse.json();

          // Build memory context string
          const memories = [];

          // Access memoryContext from the response (Flask returns {success: true, memoryContext: {...}})
          const memory = memoryData.memoryContext;

          if (memory?.reading?.vocabulary_struggles?.length > 0) {
            const words = memory.reading.vocabulary_struggles.slice(0, 3).map((v: any) => v.word).join(', ');
            memories.push(`📚 Reading vocabulary struggles: ${words}`);
          }

          if (memory?.speaking?.pronunciation_errors?.length > 0) {
            const words = memory.speaking.pronunciation_errors.slice(0, 3).map((e: any) => e.word).join(', ');
            memories.push(`🗣️ Pronunciation issues: ${words}`);
          }

          if (memory?.writing?.grammar_errors?.length > 0) {
            const errors = memory.writing.grammar_errors.slice(0, 2).map((e: any) => e.error_type).join(', ');
            memories.push(`✍️ Writing grammar issues: ${errors}`);
          }

          if (memory?.listening?.comprehension_weaknesses?.length > 0) {
            const weak = memory.listening.comprehension_weaknesses.slice(0, 2).map((w: any) => w.skill).join(', ');
            memories.push(`🎧 Listening weaknesses: ${weak}`);
          }

          if (memories.length > 0) {
            memoryContext = `\n\n🧠 STUDENT'S LEARNING HISTORY (USE THIS WHEN ASKED):\n${memories.join('\n')}\n\nWhen the student asks about their mistakes, vocabulary struggles, or what they need to practice, YOU MUST reference this specific data. For example, if they ask "What vocabulary did I struggle with?", tell them the actual words from the memory above.`;
          }
        }
      } catch (error) {
        console.error('Failed to load memory:', error);
      }
    }

    const completion = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        {
          role: "system",
          content: `You are Ms. Sarah, a warm and engaging English conversation teacher who creates a supportive speaking environment. Your personality:
          - Genuinely interested in students as people
          - Encouraging and enthusiastic about conversation
          - Natural conversationalist who loves to chat
          - Focuses on building confidence and fluency over perfection
          - Creates comfortable, judgment-free speaking practice
          - Shares personal experiences and stories when appropriate
          
          Your role is to be a speaking partner, not a critic. When students speak:
          - Respond naturally to their content first (show you're listening)
          - Ask follow-up questions about their topics
          - Share related experiences or thoughts
          - Keep conversations flowing naturally
          - If a student seems quiet or gives short answers, gently encourage them with open-ended questions
          - Create interesting conversation topics if the student doesn't have much to say
          
          ${needsMoreEngagement ? `The student seems to need more engagement. Consider asking: "${randomStarter}" or create your own engaging question to get them talking more.` : ''}

          Avoid correcting grammar, pronunciation, or mistakes unless directly asked. Your goal is natural conversation practice, not evaluation.
          ${memoryContext}

          Keep responses conversational and under 60 words. Speak like you're having coffee with a friend who happens to be learning English.`
        },
        {
          role: "user",
          content: `Student said: "${userMessage}"`
        }
      ],
      max_tokens: 150,
      temperature: 0.7,
    });

    const teacherResponse = completion.choices[0]?.message?.content || 
      "I'm so glad we're chatting! You know, I was just thinking about how much I enjoy these conversations. What's something you're passionate about lately?";

    return NextResponse.json({ response: teacherResponse });
  } catch (error) {
    console.error('English teacher API error:', error);
    return NextResponse.json({ 
      response: "Hi there! I'm Ms. Sarah, and I'm excited to have a conversation with you! What's on your mind today?" 
    }, { status: 200 });
  }
}