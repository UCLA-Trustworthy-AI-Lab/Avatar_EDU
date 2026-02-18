const FLASK_API_URL = process.env.NEXT_PUBLIC_FLASK_API_URL || 'http://localhost:5001';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const authHeader = request.headers.get('Authorization');

    if (!authHeader) {
      return new Response(JSON.stringify({
        success: false,
        error: 'Authentication required'
      }), {
        status: 401,
        headers: {
          'Content-Type': 'application/json',
        },
      });
    }

    // Proxy conversation session start to Flask backend
    const flaskResponse = await fetch(`${FLASK_API_URL}/api/conversation/streaming/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: JSON.stringify({
        topic: body.topic || 'general',
        platform: 'heygen'
      }),
    });
    
    const data = await flaskResponse.json();
    
    return new Response(JSON.stringify(data), {
      status: flaskResponse.ok ? 200 : 400,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (error) {
    console.error('Conversation session start proxy error:', error);
    return new Response(JSON.stringify({
      success: false,
      error: 'Conversation service unavailable'
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }
}