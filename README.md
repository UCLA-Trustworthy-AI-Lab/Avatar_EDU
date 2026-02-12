# 📚 Language Arts Agent - Interactive Reading Platform

An AI-powered English learning platform designed specifically for Chinese high school and college students (ages 16-20). Features interactive reading with vocabulary assistance, real-time progress tracking, and an intelligent AI chatbot for reading comprehension help.

## 🎯 **Target Audience**
- Chinese students aged 16-20
- High school and college level
- Preparing for TOEFL, IELTS, GRE exams
- Intermediate to advanced English proficiency

## ✨ **Key Features**

### 📖 **Interactive Reading**
- Click any word for instant definitions, pronunciation, and examples
- Right-click words for AI chatbot explanations in context
- Real-time reading speed tracking (WPM)
- Progress monitoring with completion percentages
- Academic texts, news articles, and exam preparation materials

### 🤖 **AI Reading Assistant**
- Contextual chatbot powered by OpenAI GPT
- Explains vocabulary in reading context
- Provides reading comprehension help
- Offers personalized reading strategies
- Adapts to student's proficiency level

### 📊 **Progress Analytics**
- Vocabulary learning statistics
- Reading speed improvement tracking
- Comprehension score analysis
- Personalized learning recommendations

## 🚀 **Quick Start**

### **Option 1: Automatic Setup (Recommended)**

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd language-arts-agent
   ```

2. **Run the startup script:**
   ```bash
   ./start.sh
   ```

3. **Add API keys when prompted:**
   - Get OpenAI API key from https://platform.openai.com/api-keys
   - Get WordsAPI key from https://rapidapi.com/dpventures/api/wordsapi (2,500 free requests/day)
   - Edit `.env` file with your keys

4. **Restart the application:**
   ```bash
   ./start.sh
   ```

### **Option 2: Manual Setup**

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   uv run python setup.py
   ```

3. **Edit `.env` file** and add your API keys:
   ```bash
   OPENAI_API_KEY=your-openai-key-here
   WORDSAPI_KEY=your-wordsapi-key-here
   ```

4. **Initialize database:**
   ```bash
   uv run python setup_db.py
   ```

5. **Start the application:**
   ```bash
   uv run python run.py
   ```

## 🌐 **Access the Application**

- **Main Page:** http://localhost:5000
- **Interactive Reading:** http://localhost:5000/reading
- **Test Student Login:** username: `student1`, password: `password123`

## 📋 **Required API Keys**

### **Essential (Free)**
- **OpenAI API Key** - For AI chatbot functionality
  - Get from: https://platform.openai.com/api-keys
  - Cost: ~$0.002 per conversation (very affordable)

- **WordsAPI Key** - For vocabulary definitions
  - Get from: https://rapidapi.com/dpventures/api/wordsapi
  - Free tier: 2,500 requests/day (sufficient for testing)

### **Optional (Advanced Features)**
- **Speechace API** - For pronunciation assessment
- **Azure Speech Services** - For speech recognition
- **HeyGen API** - For avatar conversations (future modules)

## 🎮 **How to Use**

### **Interactive Reading Interface:**

1. **Select a Reading Material** from the sidebar
   - Choose by category (Academic, News, Literature)
   - Filter by difficulty level
   - View estimated reading time

2. **Start Reading** and interact with the text:
   - **Click words** → See definitions and examples
   - **Double-click words** → Get Chinese translations
   - **Right-click words** → Ask AI chatbot for explanations

3. **Use the AI Chatbot** (robot icon, bottom-right):
   - Ask questions about the text
   - Get reading comprehension help
   - Request personalized reading tips
   - Explain difficult concepts

4. **Track Your Progress:**
   - Monitor reading speed (WPM)
   - See vocabulary learning statistics
   - Get completion percentages
   - Review performance analytics

## 🏗 **Project Structure**

```
language-arts-agent/
├── app/
│   ├── models/
│   │   ├── user.py              # Student/Teacher models
│   │   └── reading.py           # Reading session models
│   ├── services/
│   │   ├── reading_service.py   # Interactive reading logic
│   │   ├── vocabulary_service.py # Word click handling
│   │   └── reading_chatbot_service.py # AI chatbot
│   ├── api/
│   │   └── wordsapi_client.py   # WordsAPI integration
│   └── routes/
│       ├── main.py              # Landing pages
│       └── reading.py           # Reading API endpoints
├── templates/
│   ├── index.html               # Landing page
│   └── reading.html             # Interactive reading interface
├── static/
│   ├── css/reading.css          # Styles
│   └── js/reading.js            # Interactive functionality
├── setup.py                     # Environment setup
├── setup_db.py                  # Database initialization
├── start.sh                     # Startup script
└── run.py                       # Flask application runner
```

## 🔧 **Development**

### **Adding New Reading Materials**
```python
# In Python shell: uv run python -c "from app import *"
material = ReadingMaterial(
    title="Your Title",
    content="Your text content...",
    difficulty_level="intermediate",  # beginner/intermediate/advanced/expert
    category="academic",              # academic/news/literature/toefl/ielts
    word_count=len(content.split()),
    estimated_reading_time=3,
    tags=["science", "technology"],
    target_exams=["TOEFL", "IELTS"]
)
db.session.add(material)
db.session.commit()
```

### **Testing the API**
```bash
# Test vocabulary lookup
curl -X POST http://localhost:5000/api/reading/session/1/word-click \
  -H "Content-Type: application/json" \
  -d '{"word": "globalization"}'

# Test chatbot
curl -X POST http://localhost:5000/api/reading/session/1/chatbot/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is this text about?"}'
```

## 🚀 **Future Modules** (Planned in CLAUDE.md)

- **Speaking Module** - Pronunciation practice with AI avatars
- **Listening Module** - Comprehension tests with audio content
- **Writing Module** - AI-powered writing feedback
- **Conversation Module** - Free-form dialogue practice

## 🤝 **Contributing**

1. Follow the technical architecture outlined in `CLAUDE.md`
2. Use UV for package management: `uv add package-name`
3. Test with the sample student account
4. Ensure compatibility with target audience (Chinese students, ages 16-20)

## 📄 **License**

Educational use license - Designed for English language learning platforms.

---

## 🔥 **Ready to Start Learning?**

```bash
./start.sh
```

Visit http://localhost:5000/reading and begin your interactive English reading journey! 🚀