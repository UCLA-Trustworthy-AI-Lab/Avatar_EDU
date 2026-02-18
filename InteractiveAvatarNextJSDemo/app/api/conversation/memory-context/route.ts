const FLASK_API_URL = process.env.NEXT_PUBLIC_FLASK_API_URL || 'http://localhost:5001';

export async function GET(request: Request) {
  try {
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

    // Proxy memory context request to Flask backend
    const flaskResponse = await fetch(`${FLASK_API_URL}/api/conversation/memory-context`, {
      method: 'GET',
      headers: {
        'Authorization': authHeader,
      },
    });

    const data = await flaskResponse.json();

    return new Response(JSON.stringify(data), {
      status: flaskResponse.ok ? 200 : 400,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (error) {
    console.error('Memory context proxy error:', error);
    return new Response(JSON.stringify({
      success: false,
      error: 'Memory service unavailable'
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }
}
