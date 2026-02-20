# Avatar EDU - AI-Powered English Learning Platform

Avatar EDU is a comprehensive, AI-driven English Language Arts learning platform built for students who want to learning English. It integrates five interconnected learning modules — **Reading**, **Speaking**, **Listening**, **Writing**, and **Conversation** — into a unified system with cross-module memory that personalizes learning over time.

The platform combines a **Flask backend** serving four skill modules with a **Next.js frontend** powering an interactive streaming avatar conversation experience using [HeyGen](https://www.heygen.com/)'s Streaming Avatar SDK. All modules are connected through a shared student database, JWT authentication, and an Extract-Compress-Retrieve memory pipeline that tracks learning progress across sessions.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Student Browser                       │
│                                                              │
│   ┌──────────────────────┐    ┌───────────────────────────┐  │
│   │   Flask Templates    │    │   Next.js App (port 3000) │  │
│   │   (port 5001)        │    │   Streaming Avatar UI     │  │
│   │                      │    │   (HeyGen SDK + WebRTC)   │  │
│   │  - Reading Module    │    │                           │  │
│   │  - Speaking Module   │    │  - Voice Chat with Avatar │  │
│   │  - Listening Module  │    │  - English Teacher Mode   │  │
│   │  - Writing Module    │    │  - Conversation Analytics │  │
│   └──────────┬───────────┘    └─────────┬─────────────────┘  │
└──────────────┼──────────────────────────┼────────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────────────────────────────────────────┐
│                   Flask REST API (port 5001)                 │
│                                                              │
│  Auth (JWT) │ Reading │ Speaking │ Listening │ Writing │ Conv │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Memory Pipeline (per student)              │ │
│  │  Extract → Compress (every 5 sessions) → Retrieve      │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────┬────────────┬────────────┬─────────────────────┘
               │            │            │
        ┌──────┘     ┌──────┘     ┌──────┘
        ▼            ▼            ▼
   ┌─────────┐ ┌──────────┐ ┌──────────────┐
   │ SQLite/ │ │ OpenAI   │ │ Azure Speech │
   │ Postgres│ │ GPT-4o   │ │ Services     │
   └─────────┘ └──────────┘ └──────────────┘
                     │
              ┌──────┴──────┐
              ▼             ▼
        ┌──────────┐ ┌───────────┐
        │ WordsAPI │ │ HeyGen    │
        │          │ │ Streaming │
        └──────────┘ └───────────┘
```

## Learning Modules

### Reading Module
Students read academic texts, news articles, and exam prep materials with interactive vocabulary support.

- **Click any word** to see definitions, IPA pronunciation, usage examples, synonyms, and difficulty level
- **Dual reading modes**: Lock Mode (no assistance, comprehension test at end) and AI Assisted Mode (full vocabulary + chatbot)
- **AI Reading Chatbot**: Ask questions about the text, get explanations, and receive reading strategy tips
- **Vocabulary tracking**: Lookup frequency, mastery levels, and Chinese translation for complex terms
- **Real-time analytics**: Words per minute, reading progress, comprehension scores
- **Content categories**: Academic papers, news, literature, TOEFL/IELTS prep, business

### Speaking Module
Progressive pronunciation practice from individual words to full IELTS speaking responses.

- **Four-tier practice**: Words → Sentences → Paragraphs → IELTS Topic Answers
- **Azure Pronunciation Assessment**: Real-time scoring on accuracy, fluency, and completeness
- **Audio recording**: Browser-based MediaRecorder with playback and re-recording
- **Progress system**: 10-item completion flow per session with improvement tracking
- **Fallback scoring**: Mock assessment when Azure services are unavailable

### Listening Module
Audio comprehension practice with two distinct testing modes.

- **Practice mode**: Unlimited audio replays, self-paced question answering
- **Test mode**: Single-play audio with 30-second timed questions and auto-advance
- **18 topics** across 6 categories: Daily Life, Academic, Business, Travel, News, Entertainment
- **AI-generated questions**: Dynamic comprehension questions using GPT-4o based on audio transcripts
- **Azure Speech-to-Text**: Audio transcription with fallback mechanisms

### Writing Module
Structured writing practice with GPT-powered multi-dimensional analysis.

- **6 writing types**: Academic Essay, Creative Writing, Business Communication, Exam Prep (TOEFL/IELTS), Journal Entry, Technical Writing
- **Dynamic prompts**: Customized writing prompts based on topic type and difficulty level
- **GPT analysis**: Sentence-level feedback on grammar, style, vocabulary, content, and structure
- **Scoring system**: Overall score with breakdown by dimension and specific improvement suggestions
- **Auto-save drafts**: Session persistence so students never lose work
- **Real-time stats**: Word count, character count, estimated reading time

### Conversation Module (Streaming Avatar)
Real-time voice conversation with an AI avatar powered by [HeyGen Streaming Avatar SDK](https://docs.heygen.com/docs/streaming-api).

- **Streaming avatar**: Live video of an AI avatar via WebRTC, powered by HeyGen's built-in LLM
- **English Teacher mode**: Switches to OpenAI GPT-4o for pedagogically-focused responses (Ms. Sarah persona)
- **Voice chat**: Real-time speech-to-text (Deepgram via HeyGen) and text-to-speech (ElevenLabs via HeyGen)
- **Conversation analytics**: Fluency, pronunciation, vocabulary complexity, engagement scoring
- **Session reports**: Comprehensive end-of-session analysis with achievements and recommendations
- **5 topic categories**: General, Daily Life, Academic, Business, Travel

## Cross-Module Memory System

Avatar EDU includes a memory pipeline that tracks each student's learning patterns across all five modules and uses them to personalize future AI interactions.

**How it works:**

1. **Extract** — After each session, raw insights are saved (e.g., `ReadingMemoryInsight` stores vocabulary struggles, `SpeakingMemoryInsight` stores pronunciation errors)
2. **Compress** — After every 5 sessions, per-module insights are compressed into a `StudentMemoryBoard` summarizing key patterns
3. **Retrieve** — When a student starts a new session, their memory board is loaded and injected into AI prompts, so GPT-4o and the avatar can reference past struggles and strengths

This means the AI conversation partner can say things like *"I noticed you've been struggling with the word 'ubiquitous' — let's practice using it in a sentence"* based on data from the Reading module.

## Quick Start

### Prerequisites

- **Python 3.10+** with [UV](https://docs.astral.sh/uv/) package manager
- **Node.js 18+** with npm
- API keys (see [Required API Keys](#required-api-keys))

### 1. Clone the repository

```bash
git clone <repository-url>
cd Avatar_EDU
```

### 2. Set up environment variables

```bash
# Flask backend
cp .env.example .env

# Next.js frontend (avatar conversation)
cp InteractiveAvatarNextJSDemo/.env.example InteractiveAvatarNextJSDemo/.env
```

Edit both `.env` files with your API keys. See each `.env.example` for detailed instructions.

### 3. Install dependencies

```bash
# Python backend
uv sync

# Next.js frontend
cd InteractiveAvatarNextJSDemo && npm install && cd ..
```

### 4. Initialize the database

```bash
uv run python setup_db.py
```

This creates a SQLite database with demo users and sample reading materials.

### 5. Start both servers

```bash
# Option A: Use the startup script (starts both servers)
./run.sh

# Option B: Start manually in two terminals
# Terminal 1 — Flask backend (port 5001)
uv run python run.py

# Terminal 2 — Next.js frontend (port 3000)
cd InteractiveAvatarNextJSDemo && npm run dev
```

### 6. Open in browser

| URL | What it serves |
|-----|----------------|
| http://localhost:5001 | Flask app — Reading, Speaking, Listening, Writing modules |
| http://localhost:3000 | Next.js app — Streaming Avatar Conversation |

**Demo login:** username `demo_student`, password `password123`

## Required API Keys

### Required

| API | Used by | Purpose | Get from |
|-----|---------|---------|----------|
| **OpenAI** | All modules | AI chatbot, question generation, writing analysis, teacher mode | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| **HeyGen** | Conversation | Streaming avatar video, built-in LLM, voice chat | [app.heygen.com/settings](https://app.heygen.com/settings?nav=API) |

### Optional

| API | Used by | Purpose | Get from |
|-----|---------|---------|----------|
| **Azure Speech** | Speaking, Listening | Pronunciation assessment, speech-to-text | [portal.azure.com](https://portal.azure.com) (Cognitive Services → Speech) |
| **WordsAPI** | Reading | Vocabulary definitions, examples, synonyms | [rapidapi.com/wordsapi](https://rapidapi.com/dpventures/api/wordsapi) (free: 2,500 req/day) |

All modules include **fallback responses** when optional APIs are unavailable, so the app remains functional with just OpenAI and HeyGen keys.

## Project Structure

```
Avatar_EDU/
├── app/
│   ├── models/              # SQLAlchemy models (user, session, reading, memory, etc.)
│   ├── services/            # Business logic per module
│   │   ├── reading_service.py
│   │   ├── speaking_service.py
│   │   ├── listening_service.py
│   │   ├── writing_service.py
│   │   ├── conversation_service.py
│   │   ├── vocabulary_service.py
│   │   └── reading_chatbot_service.py
│   ├── api/                 # External API clients
│   │   ├── openai_client.py
│   │   ├── heygen_client.py
│   │   ├── azure_speech_client.py
│   │   └── wordsapi_client.py
│   └── routes/              # Flask REST endpoints (46+ endpoints)
│       ├── auth.py          # JWT login/register/profile
│       ├── reading.py       # 15 reading endpoints
│       ├── speaking.py      # 8 speaking endpoints
│       ├── listening.py     # 6 listening endpoints
│       ├── writing.py       # 5 writing endpoints
│       └── conversation.py  # 12 conversation endpoints
├── templates/               # Flask HTML templates (Bootstrap 5)
├── static/                  # CSS + JavaScript assets
├── InteractiveAvatarNextJSDemo/  # Next.js streaming avatar frontend
│   ├── components/          # React components (avatar, analytics, auth)
│   └── app/api/             # Next.js API routes (proxy to Flask)
├── config/                  # Flask configuration (dev/test/prod)
├── .env.example             # Environment template
├── setup_db.py              # Database initialization + seed data
├── run.py                   # Flask entry point
└── run.sh                   # Start both servers
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Flask, SQLAlchemy, Flask-JWT-Extended, SQLite (dev) / PostgreSQL (prod) |
| **Frontend (skills)** | Bootstrap 5, vanilla JavaScript, HTML templates |
| **Frontend (avatar)** | Next.js 14, React, TypeScript, [HeyGen Streaming Avatar SDK](https://www.npmjs.com/package/@heygen/streaming-avatar) |
| **AI / LLM** | OpenAI GPT-4o (text generation), HeyGen built-in LLM (avatar conversation) |
| **Speech** | Azure Speech Services (pronunciation + STT), Deepgram (STT via HeyGen), ElevenLabs (TTS via HeyGen) |
| **Vocabulary** | WordsAPI (definitions, examples, synonyms) |
| **Package Management** | UV (Python), npm (Node.js) |
| **Real-time** | WebRTC (avatar video), WebSocket (voice chat) |

## Acknowledgments

- [HeyGen](https://www.heygen.com/) — Streaming Avatar SDK for real-time AI avatar video conversations
- [OpenAI](https://openai.com/) — GPT-4o for AI-powered teaching, analysis, and question generation
- [Microsoft Azure](https://azure.microsoft.com/en-us/products/ai-services/ai-speech) — Speech Services for pronunciation assessment and speech-to-text
- [WordsAPI](https://www.wordsapi.com/) — Comprehensive vocabulary data
- [ElevenLabs](https://elevenlabs.io/) — Text-to-speech (via HeyGen integration)
- [Deepgram](https://deepgram.com/) — Speech-to-text (via HeyGen integration)

## License

Educational use license — Designed for English language learning platforms.
