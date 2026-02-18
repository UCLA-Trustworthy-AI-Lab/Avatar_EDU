const FLASK_API_URL = process.env.NEXT_PUBLIC_FLASK_API_URL || 'http://localhost:5001';

export async function POST(request: Request) {
  try {
    const body = await request.json();

    // Proxy authentication request to Flask backend
    const flaskResponse = await fetch(`${FLASK_API_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    const data = await flaskResponse.json();
    
    if (flaskResponse.ok && data.access_token) {
      // Return the auth token and user info
      return new Response(JSON.stringify({
        success: true,
        token: data.access_token,
        user: {
          id: data.user_id,
          username: data.username,
          user_type: data.user_type
        },
        message: 'Login successful'
      }), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
        },
      });
    } else {
      return new Response(JSON.stringify({
        success: false,
        error: data.error || 'Login failed'
      }), {
        status: 401,
        headers: {
          'Content-Type': 'application/json',
        },
      });
    }
  } catch (error) {
    console.error('Login proxy error:', error);
    return new Response(JSON.stringify({
      success: false,
      error: 'Authentication service unavailable'
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }
}