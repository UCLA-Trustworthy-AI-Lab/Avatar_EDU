# Avatar EDU - Interactive Streaming Avatar Conversation

This is the **Next.js frontend** for Avatar EDU's Conversation module. It provides a real-time streaming avatar conversation experience powered by [HeyGen's Streaming Avatar SDK](https://docs.heygen.com/docs/streaming-api), enabling students to practice English speaking with an AI-driven virtual teacher.

This project was built on top of HeyGen's [Interactive Avatar NextJS Demo](https://github.com/HeyGen-Official/InteractiveAvatarNextJSDemo) and extended with authentication, conversation analytics, English teacher mode, and integration with the Avatar EDU Flask backend.

![Interactive Avatar Demo](./public/demo.png)

## How It Works

```
Student speaks (microphone)
        │
        ▼
┌─────────────────────┐
│  Deepgram STT       │  (speech-to-text, via HeyGen)
│  converts voice     │
│  to text             │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐     ┌──────────────────────┐
│  HeyGen Built-in    │ OR  │  OpenAI GPT-4o       │
│  LLM (default mode) │     │  (English Teacher     │
│                     │     │   mode - Ms. Sarah)   │
└────────┬────────────┘     └────────┬─────────────┘
         │                           │
         └───────────┬───────────────┘
                     ▼
         ┌───────────────────────┐
         │  ElevenLabs TTS       │  (text-to-speech, via HeyGen)
         │  generates voice      │
         └───────────┬───────────┘
                     ▼
         ┌───────────────────────┐
         │  HeyGen Streaming     │  (avatar video via WebRTC)
         │  Avatar renders       │
         │  lip-synced video     │
         └───────────────────────┘
                     │
                     ▼
           Student sees and hears
           the avatar's response
```

### Two Conversation Modes

| Mode | LLM Used | Behavior |
|------|----------|----------|
| **Default (HeyGen)** | HeyGen's built-in LLM | General conversation, responds naturally based on a knowledge base prompt |
| **English Teacher** | OpenAI GPT-4o | Pedagogically-focused responses as "Ms. Sarah", an encouraging English conversation teacher. Pulls from the student's cross-module learning memory for personalized feedback |

## Features

- **Streaming Avatar**: Real-time AI avatar video via WebRTC with lip-synced speech
- **Voice Chat**: Speak naturally through your microphone; Deepgram transcribes in real-time
- **English Teacher Mode**: Toggle to switch from HeyGen's LLM to GPT-4o with a teaching-focused persona
- **Conversation Topics**: 5 categories (General, Daily Life, Academic, Business, Travel) with guided prompts
- **Conversation Analytics**: Real-time tracking of fluency, vocabulary complexity, engagement, and conversation flow
- **Session Reports**: End-of-session analysis with scores, achievements, and improvement recommendations
- **Learning Memory**: Retrieves the student's past learning data (vocabulary struggles, pronunciation errors, grammar issues) from all five Avatar EDU modules and injects it into AI prompts
- **Authentication**: JWT-based login connected to the Flask backend's student database

## Setup

### Prerequisites

- Node.js 18+
- npm
- A running Avatar EDU Flask backend (port 5001) — see the [root README](../README.md)

### 1. Install dependencies

```bash
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```env
# Required
HEYGEN_API_KEY=your-heygen-api-key
OPENAI_API_KEY=your-openai-api-key

# Backend connection
NEXT_PUBLIC_FLASK_API_URL=http://localhost:5001
```

### 3. Start the development server

```bash
npm run dev
```

Open http://localhost:3000 in your browser.

### 4. Log in

Use your Avatar EDU student account (e.g., `demo_student` / `password123`).

## API Keys

| Key | Required | Purpose |
|-----|----------|---------|
| `HEYGEN_API_KEY` | Yes | Streaming avatar session, built-in LLM, Deepgram STT, ElevenLabs TTS |
| `OPENAI_API_KEY` | Yes (for Teacher mode) | GPT-4o responses in English Teacher mode |

Get your HeyGen API key from [app.heygen.com/settings](https://app.heygen.com/settings?nav=API). You need an Enterprise or Trial plan for Streaming Avatar access.

## Project Structure

```
InteractiveAvatarNextJSDemo/
├── app/
│   ├── api/                    # Next.js API routes
│   │   ├── get-access-token/   # Generate HeyGen session tokens
│   │   ├── english-teacher/    # GPT-4o English teacher endpoint
│   │   ├── auth/login/         # Proxy login to Flask backend
│   │   └── conversation/       # Proxy conversation analytics to Flask
│   ├── lib/constants.ts        # Avatar IDs, voice configs
│   └── page.tsx                # Main page
├── components/
│   ├── InteractiveAvatar.tsx   # Main avatar component
│   ├── AvatarSession/          # Video display, controls, message history
│   ├── analytics/              # Conversation scoring and display
│   ├── auth/                   # Login UI and auth context
│   ├── logic/                  # Hooks for streaming session and voice chat
│   ├── TeacherModeToggle.tsx   # Switch between HeyGen LLM and GPT-4o
│   └── ConversationTopics.tsx  # Topic selection UI
└── public/
    └── demo.png                # Demo screenshot
```

## Customizing the Avatar

You can use any HeyGen Interactive Avatar. To change the default:

1. Go to [labs.heygen.com/interactive-avatar](https://labs.heygen.com/interactive-avatar)
2. Click **Select Avatar** and copy the avatar ID
3. Update the `AVATARS` array in `app/lib/constants.ts`

You can also create custom avatars at the same page by clicking **Create Interactive Avatar**.

## Acknowledgments

- [HeyGen](https://www.heygen.com/) — Streaming Avatar SDK, built-in LLM, WebRTC infrastructure
- [HeyGen InteractiveAvatarNextJSDemo](https://github.com/HeyGen-Official/InteractiveAvatarNextJSDemo) — Original demo this project was built upon
- [OpenAI](https://openai.com/) — GPT-4o for English Teacher mode
- [Deepgram](https://deepgram.com/) — Speech-to-text (integrated via HeyGen)
- [ElevenLabs](https://elevenlabs.io/) — Text-to-speech (integrated via HeyGen)

For more about HeyGen's Interactive Avatar API, see the [Interactive Avatar 101 Guide](https://help.heygen.com/en/articles/9182113-interactive-avatar-101-your-ultimate-guide).
