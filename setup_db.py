#!/usr/bin/env python3
"""
Database setup script for Language Arts Agent
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app import create_app, db
from app.models.user import User, Student, Teacher
from app.models.reading import ReadingMaterial, ReadingSession, VocabularyInteraction, ReadingProgress
from app.models.speaking import SpeakingPracticeContent

def create_sample_data():
    """Create some sample reading materials for testing"""
    
    # Sample academic article
    academic_text = """
    The phenomenon of globalization has fundamentally transformed the landscape of international business and economic development. As multinational corporations expand their operations across borders, they encounter diverse cultural contexts that necessitate adaptive strategies. This process of cultural adaptation involves not merely translating products and services, but rather understanding the intricate nuances of local customs, values, and consumer behaviors.

    Research indicates that successful international expansion requires comprehensive market analysis and cultural intelligence. Companies that invest in understanding local preferences demonstrate significantly higher success rates in foreign markets. Furthermore, the integration of technology has accelerated the pace of globalization, enabling rapid communication and data exchange across continents.

    However, globalization also presents considerable challenges. Economic disparities between developed and developing nations can exacerbate existing inequalities. Additionally, the homogenization of cultures raises concerns about the preservation of local traditions and languages. These complex dynamics require careful consideration from policymakers and business leaders alike.
    """
    
    # Sample news article
    news_text = """
    Scientists at leading universities have made breakthrough discoveries in renewable energy technology that could revolutionize how we power our cities. The new solar panel design incorporates advanced materials that increase efficiency by 40% while reducing manufacturing costs.

    Dr. Sarah Chen, the lead researcher, explained that the innovation lies in the unique arrangement of photovoltaic cells that can capture light from multiple angles. "This technology represents a significant step forward in making solar energy more accessible and affordable for communities worldwide," she stated during yesterday's press conference.

    The research team collaborated with engineers from three different countries, demonstrating the power of international scientific cooperation. Initial testing has shown promising results, with pilot installations already planned for several cities across Asia and Europe.

    Industry experts predict that this breakthrough could accelerate the global transition to renewable energy sources. The technology is expected to be commercially available within the next two years, pending regulatory approval and large-scale testing.
    """
    
    materials = [
        ReadingMaterial(
            title="Globalization and Cultural Adaptation in International Business",
            content=academic_text,
            difficulty_level="advanced",
            category="academic",
            word_count=len(academic_text.split()),
            estimated_reading_time=3,
            tags=["business", "globalization", "economics", "culture"],
            target_exams=["TOEFL", "IELTS", "GRE"]
        ),
        ReadingMaterial(
            title="Breakthrough in Solar Energy Technology",
            content=news_text,
            difficulty_level="intermediate",
            category="news",
            word_count=len(news_text.split()),
            estimated_reading_time=2,
            tags=["science", "technology", "environment", "energy"],
            target_exams=["TOEFL", "IELTS"]
        )
    ]
    
    for material in materials:
        existing = ReadingMaterial.query.filter_by(title=material.title).first()
        if not existing:
            db.session.add(material)
    
    db.session.commit()
    print("✅ Sample reading materials created")

    # Create speaking practice content
    create_speaking_content()

def create_speaking_content():
    """Create sample speaking practice content for all three types"""

    # Academic Vocabulary Words
    academic_words = [
        {"word": "analyze", "phonetic": "/ˈæn.ə.laɪz/", "context": "To examine something in detail to understand it better"},
        {"word": "comprehensive", "phonetic": "/ˌkɒm.prɪˈhen.sɪv/", "context": "Including everything that is relevant; complete"},
        {"word": "demonstrate", "phonetic": "/ˈdem.ən.streɪt/", "context": "To show clearly by giving proof or evidence"},
        {"word": "fundamental", "phonetic": "/ˌfʌn.dəˈmen.təl/", "context": "Basic and essential; forming the foundation"},
        {"word": "significance", "phonetic": "/sɪɡˈnɪf.ɪ.kəns/", "context": "The importance or meaning of something"},
        {"word": "hypothesis", "phonetic": "/haɪˈpɒθ.ə.sɪs/", "context": "A proposed explanation that can be tested"},
        {"word": "methodology", "phonetic": "/ˌmeθ.əˈdɒl.ə.dʒi/", "context": "A system of methods used in research"},
        {"word": "subsequent", "phonetic": "/ˈsʌb.sɪ.kwənt/", "context": "Coming after something in time or order"},
        {"word": "preliminary", "phonetic": "/prɪˈlɪm.ɪ.nər.i/", "context": "Coming before the main part; introductory"},
        {"word": "parameters", "phonetic": "/pəˈræm.ɪ.təz/", "context": "The limits or boundaries that define a system"}
    ]

    # Daily Conversation Words
    daily_words = [
        {"word": "restaurant", "phonetic": "/ˈres.tər.ɑːnt/", "context": "A place where meals are prepared and served"},
        {"word": "appointment", "phonetic": "/əˈpɔɪnt.mənt/", "context": "A scheduled meeting with someone"},
        {"word": "grocery", "phonetic": "/ˈɡroʊ.sər.i/", "context": "Food and household items sold in a store"},
        {"word": "transportation", "phonetic": "/ˌtræn.spərˈteɪ.ʃən/", "context": "The process of moving people or things"},
        {"word": "conversation", "phonetic": "/ˌkɑːn.vərˈseɪ.ʃən/", "context": "An informal talk between two or more people"},
        {"word": "neighborhood", "phonetic": "/ˈneɪ.bər.hʊd/", "context": "An area of a city or town where people live"},
        {"word": "emergency", "phonetic": "/ɪˈmɜːr.dʒən.si/", "context": "A serious situation requiring immediate action"},
        {"word": "temperature", "phonetic": "/ˈtem.pər.ə.tʃər/", "context": "How hot or cold something is"},
        {"word": "celebration", "phonetic": "/ˌsel.əˈbreɪ.ʃən/", "context": "A special event to mark an important occasion"},
        {"word": "invitation", "phonetic": "/ˌɪn.vɪˈteɪ.ʃən/", "context": "A request to participate in an event"}
    ]

    # Business Words
    business_words = [
        {"word": "negotiation", "phonetic": "/nɪˌɡoʊ.ʃiˈeɪ.ʃən/", "context": "Discussion to reach an agreement"},
        {"word": "presentation", "phonetic": "/ˌprez.ənˈteɪ.ʃən/", "context": "A speech or talk introducing a topic"},
        {"word": "collaboration", "phonetic": "/kəˌlæb.əˈreɪ.ʃən/", "context": "Working together on a project"},
        {"word": "productivity", "phonetic": "/ˌproʊ.dʌkˈtɪv.ə.ti/", "context": "The effectiveness of effort in production"},
        {"word": "efficiency", "phonetic": "/ɪˈfɪʃ.ən.si/", "context": "Achieving maximum output with minimum input"}
    ]

    # Academic Discussion Sentences
    academic_sentences = [
        "The research methodology employed in this study demonstrates significant validity.",
        "Furthermore, the preliminary results indicate a strong correlation between variables.",
        "This hypothesis requires comprehensive analysis before drawing conclusions.",
        "The fundamental principles underlying this theory need careful examination.",
        "Subsequently, we must consider the broader implications of these findings."
    ]

    # Daily Conversation Sentences
    daily_sentences = [
        "Could you please tell me how to get to the nearest grocery store?",
        "I'd like to make an appointment with the doctor for next Tuesday.",
        "The weather forecast shows the temperature will drop significantly tomorrow.",
        "We're planning a celebration for my sister's graduation next month.",
        "Thank you for the invitation to your neighborhood barbecue party."
    ]

    # Business Communication Sentences
    business_sentences = [
        "Our team's productivity has increased by twenty percent this quarter.",
        "I'd like to schedule a presentation for the new marketing strategy.",
        "Effective collaboration between departments is essential for success.",
        "We need to improve efficiency in our manufacturing processes.",
        "The negotiation with our international partners was very successful."
    ]

    # Self-Introduction Paragraphs
    intro_paragraphs = [
        "Hello, my name is [Student Name]. I am currently studying at [University Name] majoring in international business. I chose this field because I'm passionate about global commerce and cultural exchange. In my free time, I enjoy reading about different cultures and practicing languages. My goal is to work for a multinational company where I can use my communication skills to bridge cultural differences.",

        "Good morning, everyone. I'm [Student Name], and I'm a sophomore at [University Name]. I'm pursuing a degree in computer science with a focus on artificial intelligence. What attracted me to this field is the potential to solve complex problems using technology. Outside of academics, I volunteer at local coding workshops for high school students. I hope to develop innovative AI solutions that can benefit society."
    ]

    # Academic Discussion Paragraphs
    academic_paragraphs = [
        "The phenomenon of climate change represents one of the most significant challenges facing humanity today. Scientific evidence overwhelmingly demonstrates that human activities, particularly the emission of greenhouse gases, are driving unprecedented changes in global weather patterns. This crisis requires immediate and coordinated international action. Governments, businesses, and individuals must work together to implement sustainable practices and reduce carbon emissions. The consequences of inaction will be severe and irreversible for future generations.",

        "The digital revolution has fundamentally transformed modern education systems worldwide. Online learning platforms now provide unprecedented access to educational resources, enabling students from diverse backgrounds to pursue higher education. However, this technological shift also presents challenges, including the digital divide and concerns about academic integrity. Educational institutions must adapt their pedagogical approaches to effectively integrate technology while maintaining the quality and authenticity of learning experiences."
    ]

    # Business Presentation Paragraphs
    business_paragraphs = [
        "Our company's expansion into Asian markets represents a strategic opportunity for significant growth. Market research indicates strong demand for our products in this region, particularly in China and India. To succeed, we must adapt our marketing strategies to local cultures and consumer preferences. This expansion will require substantial investment in regional partnerships and cultural training for our international teams. The projected return on investment over five years shows considerable potential for profitability.",

        "Implementing sustainable business practices is no longer optional in today's competitive marketplace. Consumers increasingly prefer companies that demonstrate environmental responsibility and social consciousness. Our sustainability initiative includes reducing waste, using renewable energy sources, and supporting local communities. These practices not only benefit the environment but also improve our brand reputation and reduce operational costs. We expect to see positive financial returns within the next three years."
    ]

    # Create word content
    speaking_content = []

    # Add academic vocabulary words
    for word_data in academic_words:
        content = SpeakingPracticeContent(
            practice_type='word',
            content_text=word_data['word'],
            phonetic_transcription=word_data['phonetic'],
            difficulty_level='beginner',
            category='academic_vocabulary',
            academic_level='undergraduate',
            exam_type='TOEFL',
            context_hint=word_data['context']
        )
        speaking_content.append(content)

    # Add daily conversation words
    for word_data in daily_words:
        content = SpeakingPracticeContent(
            practice_type='word',
            content_text=word_data['word'],
            phonetic_transcription=word_data['phonetic'],
            difficulty_level='beginner',
            category='daily_conversation',
            academic_level='high_school',
            context_hint=word_data['context']
        )
        speaking_content.append(content)

    # Add business words
    for word_data in business_words:
        content = SpeakingPracticeContent(
            practice_type='word',
            content_text=word_data['word'],
            phonetic_transcription=word_data['phonetic'],
            difficulty_level='advanced',
            category='business_english',
            academic_level='graduate',
            exam_type='IELTS',
            context_hint=word_data['context']
        )
        speaking_content.append(content)

    # Add academic sentences
    for sentence in academic_sentences:
        content = SpeakingPracticeContent(
            practice_type='sentence',
            content_text=sentence,
            difficulty_level='intermediate',
            category='academic_discussion',
            academic_level='undergraduate',
            exam_type='TOEFL',
            context_hint='Practice academic speaking and pronunciation'
        )
        speaking_content.append(content)

    # Add daily conversation sentences
    for sentence in daily_sentences:
        content = SpeakingPracticeContent(
            practice_type='sentence',
            content_text=sentence,
            difficulty_level='beginner',
            category='daily_conversation',
            academic_level='high_school',
            context_hint='Practice everyday English conversations'
        )
        speaking_content.append(content)

    # Add business sentences
    for sentence in business_sentences:
        content = SpeakingPracticeContent(
            practice_type='sentence',
            content_text=sentence,
            difficulty_level='advanced',
            category='business_communication',
            academic_level='graduate',
            exam_type='IELTS',
            context_hint='Practice professional business communication'
        )
        speaking_content.append(content)

    # Add introduction paragraphs
    for paragraph in intro_paragraphs:
        content = SpeakingPracticeContent(
            practice_type='paragraph',
            content_text=paragraph,
            difficulty_level='beginner',
            category='self_introduction',
            academic_level='high_school',
            context_hint='Practice introducing yourself in academic or professional settings'
        )
        speaking_content.append(content)

    # Add academic paragraphs
    for paragraph in academic_paragraphs:
        content = SpeakingPracticeContent(
            practice_type='paragraph',
            content_text=paragraph,
            difficulty_level='advanced',
            category='academic_discussion',
            academic_level='undergraduate',
            exam_type='TOEFL',
            context_hint='Practice presenting academic arguments and analysis'
        )
        speaking_content.append(content)

    # Add business paragraphs
    for paragraph in business_paragraphs:
        content = SpeakingPracticeContent(
            practice_type='paragraph',
            content_text=paragraph,
            difficulty_level='expert',
            category='business_presentation',
            academic_level='graduate',
            exam_type='IELTS',
            context_hint='Practice professional business presentations'
        )
        speaking_content.append(content)

    # Create topic content for IELTS-style practice
    create_topic_content(speaking_content)

    # Save all content to database
    for content in speaking_content:
        existing = SpeakingPracticeContent.query.filter_by(
            practice_type=content.practice_type,
            content_text=content.content_text
        ).first()
        if not existing:
            db.session.add(content)

    db.session.commit()
    print("✅ Sample speaking practice content created")
    print(f"   📝 {len([c for c in speaking_content if c.practice_type == 'word'])} word practice items")
    print(f"   📝 {len([c for c in speaking_content if c.practice_type == 'sentence'])} sentence practice items")
    print(f"   📝 {len([c for c in speaking_content if c.practice_type == 'paragraph'])} paragraph practice items")
    print(f"   📝 {len([c for c in speaking_content if c.practice_type == 'topic'])} topic practice items")

def create_topic_content(speaking_content):
    """Create topic content for IELTS-style speaking practice"""

    # Topic content by category
    topic_content = {
        'general': [
            "Describe your favorite hobby and explain why you enjoy it.",
            "Talk about a memorable experience from your childhood.",
            "Describe a place you would like to visit and explain why.",
            "Discuss the importance of friendship in your life.",
            "Describe a skill you would like to learn and explain why.",
            "Talk about a book or movie that influenced you.",
            "Describe your ideal weekend and what you would do.",
            "Discuss a problem in your community and suggest solutions."
        ],
        'education': [
            "Describe your ideal school or university.",
            "Discuss the role of technology in modern education.",
            "Talk about a subject you found challenging and how you overcame it.",
            "Explain the benefits of studying abroad.",
            "Describe an effective teacher you've had.",
            "Discuss the importance of lifelong learning.",
            "Talk about changes you would make to the education system.",
            "Describe the benefits of online learning."
        ],
        'technology': [
            "Describe how technology has changed daily life.",
            "Discuss the advantages and disadvantages of social media.",
            "Talk about a piece of technology you couldn't live without.",
            "Explain how artificial intelligence might affect jobs in the future.",
            "Describe how people communicated before smartphones.",
            "Discuss the impact of the internet on education.",
            "Talk about privacy concerns in the digital age.",
            "Describe how technology has changed entertainment."
        ],
        'environment': [
            "Describe what individuals can do to protect the environment.",
            "Discuss the effects of climate change on your country.",
            "Talk about renewable energy sources.",
            "Explain the importance of recycling.",
            "Describe environmental problems in urban areas.",
            "Discuss the role of governments in environmental protection.",
            "Talk about sustainable transportation options.",
            "Describe the benefits of organic farming."
        ],
        'culture': [
            "Describe an important festival or celebration in your culture.",
            "Discuss how globalization affects local traditions.",
            "Talk about cultural differences you've observed.",
            "Explain the importance of preserving cultural heritage.",
            "Describe traditional food from your country.",
            "Discuss the role of museums in preserving culture.",
            "Talk about traditional arts and crafts in your region.",
            "Describe how young people can learn about their culture."
        ],
        'work': [
            "Describe your ideal job and explain why.",
            "Discuss the importance of work-life balance.",
            "Talk about skills that are important in today's workplace.",
            "Explain how remote work has changed the modern workplace.",
            "Describe the qualities of a good manager.",
            "Discuss the challenges facing young job seekers.",
            "Talk about the importance of teamwork in the workplace.",
            "Describe how people will work in the future."
        ],
        'travel': [
            "Describe a place you have visited that impressed you.",
            "Discuss the benefits of traveling to different countries.",
            "Talk about your dream vacation destination.",
            "Explain how travel can change a person's perspective.",
            "Describe the differences between traveling alone and in groups.",
            "Discuss the impact of tourism on local communities.",
            "Talk about budget travel vs. luxury travel.",
            "Describe how transportation has made travel easier."
        ],
        'health': [
            "Describe how you maintain a healthy lifestyle.",
            "Discuss the importance of mental health awareness.",
            "Talk about a sport or exercise you enjoy.",
            "Explain the role of diet in maintaining good health.",
            "Describe the healthcare system in your country.",
            "Discuss the benefits of regular medical checkups.",
            "Talk about traditional medicine vs. modern medicine.",
            "Describe how stress affects people's health."
        ]
    }

    # Create topic practice content for each category and difficulty
    for category, topics in topic_content.items():
        for i, topic_text in enumerate(topics):
            # Assign difficulty based on complexity and position
            if i < 3:
                difficulty = 'beginner'
                academic_level = 'high_school'
            elif i < 6:
                difficulty = 'intermediate'
                academic_level = 'undergraduate'
            else:
                difficulty = 'advanced'
                academic_level = 'graduate'

            content = SpeakingPracticeContent(
                practice_type='topic',
                content_text=topic_text,
                difficulty_level=difficulty,
                category=category,
                academic_level=academic_level,
                exam_type='IELTS',
                context_hint=f'IELTS-style speaking topic: 90 seconds to prepare, 1 minute to speak'
            )
            speaking_content.append(content)

def setup_database():
    """Initialize the database with tables and sample data"""
    
    print("🗄️  Setting up database...")
    
    # Create all tables
    with app.app_context():
        db.create_all()
        print("✅ Database tables created")
        
        # Create sample data
        create_sample_data()
        
        print("✅ Database setup complete!")
        print("\n📖 Sample content added:")
        print("Reading Materials:")
        print("  1. 'Globalization and Cultural Adaptation in International Business' (Advanced)")
        print("  2. 'Breakthrough in Solar Energy Technology' (Intermediate)")
        print("Speaking Practice Content:")
        print("  • Academic vocabulary, daily conversation, and business words")
        print("  • Sentences for academic discussion, daily conversation, and business communication")
        print("  • Paragraphs for self-introduction, academic discussion, and business presentations")

if __name__ == "__main__":
    # For development, we can use SQLite instead of PostgreSQL
    os.environ['DATABASE_URL'] = 'sqlite:///language_arts.db'
    
    app = create_app()
    setup_database()