#!/usr/bin/env python3
"""
Script to add more reading materials to the database
"""

import os
from app import create_app, db
from app.models.reading import ReadingMaterial

def add_more_materials():
    """Add additional reading materials for better testing"""
    
    # Literature sample
    literature_text = """
    In the quiet town of Millbrook, autumn arrived with a symphony of colors that painted the landscape in shades of gold and crimson. Emma walked through the park, her footsteps crunching softly on the fallen leaves that carpeted the winding path.

    She had always found solace in this place, especially during times of uncertainty. Today was no different. The acceptance letter from the university lay folded in her jacket pocket, its weight both thrilling and terrifying. It represented everything she had worked toward, yet it also meant leaving behind everything familiar.

    As she paused by the old oak tree where she had spent countless hours reading as a child, Emma reflected on the journey that had brought her here. The late nights studying, the support of her family, and the dreams that had seemed impossible just a few years ago. Now, those dreams were within reach.

    A gentle breeze stirred the branches above, sending a cascade of leaves dancing around her. In that moment, Emma understood that change, like the seasons, was natural and necessary. She pulled out the letter and read it once more, a smile spreading across her face as she embraced the adventure that awaited her.
    """
    
    # Business English sample
    business_text = """
    Effective communication in the modern workplace requires a combination of traditional skills and digital literacy. As organizations become increasingly global and remote work becomes more prevalent, professionals must adapt their communication strategies to maintain productivity and build strong relationships with colleagues.

    Email remains a primary communication tool, but its effectiveness depends on clarity and conciseness. Successful business emails follow a clear structure: a specific subject line, a brief introduction, the main message with supporting details, and a clear call to action. This format ensures that recipients can quickly understand the purpose and respond appropriately.

    Video conferencing has transformed how teams collaborate across distances. However, virtual meetings present unique challenges, including technical difficulties, reduced non-verbal communication, and potential distractions. To maximize effectiveness, participants should prepare thoroughly, test technology in advance, and establish clear protocols for interaction.

    The rise of instant messaging platforms has created new opportunities for real-time collaboration while also introducing challenges related to information overload and boundary setting. Organizations must establish guidelines that balance accessibility with respect for personal time and focused work periods.
    """
    
    # Science article
    science_text = """
    Recent advances in artificial intelligence have sparked both excitement and concern among scientists, ethicists, and the general public. Machine learning algorithms can now perform complex tasks that were once thought to be exclusively human, from diagnosing medical conditions to creating artistic works.

    The technology behind these breakthroughs relies on neural networks that mimic the structure of the human brain. These systems process vast amounts of data to identify patterns and make predictions with remarkable accuracy. In healthcare, AI systems can analyze medical images faster than human radiologists, potentially detecting diseases at earlier stages.

    However, the rapid development of AI also raises important ethical questions. Issues of privacy, bias, and job displacement require careful consideration. Researchers emphasize the importance of developing AI systems that are transparent, fair, and aligned with human values.

    Looking toward the future, experts predict that AI will continue to transform various industries while creating new opportunities for human-AI collaboration. The key lies in ensuring that these powerful technologies are developed and deployed responsibly, with appropriate oversight and consideration for their societal impact.
    """
    
    # TOEFL preparation text
    toefl_text = """
    Urban planning in the 21st century faces unprecedented challenges as cities worldwide experience rapid population growth and environmental pressures. Modern urban planners must balance the need for housing, transportation, and commercial development while preserving green spaces and ensuring sustainability.

    Smart city initiatives represent one approach to addressing these challenges. These projects integrate technology into urban infrastructure to improve efficiency and quality of life. Examples include traffic management systems that reduce congestion, smart grids that optimize energy distribution, and digital platforms that enhance citizen services.

    Public transportation plays a crucial role in sustainable urban development. Well-designed transit systems can reduce air pollution, decrease traffic congestion, and provide affordable mobility options for residents. Cities like Copenhagen and Singapore have demonstrated how investment in public transportation can transform urban environments.

    Green building standards have become increasingly important in urban planning. These guidelines promote energy efficiency, water conservation, and the use of sustainable materials. Buildings that meet these standards not only reduce environmental impact but also provide healthier living and working environments for occupants.

    The success of urban planning initiatives depends largely on community engagement and political support. Planners must work closely with residents, businesses, and government officials to develop solutions that meet diverse needs while advancing long-term sustainability goals.
    """
    
    # News article about technology
    tech_news_text = """
    A major tech company announced yesterday that it will invest $5 billion in developing quantum computing technology over the next five years. This investment represents one of the largest commitments to quantum research by a private corporation and signals growing confidence in the commercial potential of this emerging technology.

    Quantum computers use the principles of quantum mechanics to process information in ways that classical computers cannot. While still in early stages of development, these machines could eventually solve complex problems in fields such as drug discovery, financial modeling, and climate research.

    The announcement comes as governments and companies worldwide race to achieve "quantum supremacy" – the point at which quantum computers can perform calculations that are impossible for traditional computers. China and the United States have already invested heavily in quantum research, viewing it as critical to future technological leadership.

    Industry analysts note that practical quantum computers are still years away from widespread commercial use. Current quantum systems require extremely cold temperatures and are highly sensitive to environmental interference. However, recent breakthroughs have demonstrated significant progress in overcoming these technical challenges.

    The investment will fund research partnerships with leading universities and the construction of new quantum laboratories. Company executives expressed optimism that these efforts will accelerate the development of practical quantum applications and establish their organization as a leader in this transformative technology.
    """
    
    materials = [
        ReadingMaterial(
            title="A Season of Change",
            content=literature_text,
            difficulty_level="intermediate",
            category="literature",
            word_count=len(literature_text.split()),
            estimated_reading_time=2,
            tags=["literature", "personal growth", "change", "reflection"],
            target_exams=["TOEFL", "IELTS"]
        ),
        ReadingMaterial(
            title="Communication in the Digital Workplace",
            content=business_text,
            difficulty_level="advanced",
            category="business",
            word_count=len(business_text.split()),
            estimated_reading_time=3,
            tags=["business", "communication", "workplace", "technology"],
            target_exams=["TOEFL", "IELTS", "GRE"]
        ),
        ReadingMaterial(
            title="The Future of Artificial Intelligence",
            content=science_text,
            difficulty_level="advanced",
            category="academic",
            word_count=len(science_text.split()),
            estimated_reading_time=3,
            tags=["science", "AI", "technology", "ethics"],
            target_exams=["TOEFL", "IELTS", "GRE"]
        ),
        ReadingMaterial(
            title="Modern Urban Planning Challenges",
            content=toefl_text,
            difficulty_level="advanced",
            category="toefl",
            word_count=len(toefl_text.split()),
            estimated_reading_time=4,
            tags=["urban planning", "sustainability", "environment", "cities"],
            target_exams=["TOEFL", "GRE"]
        ),
        ReadingMaterial(
            title="Quantum Computing Investment Breakthrough",
            content=tech_news_text,
            difficulty_level="intermediate",
            category="news",
            word_count=len(tech_news_text.split()),
            estimated_reading_time=3,
            tags=["technology", "quantum computing", "investment", "research"],
            target_exams=["TOEFL", "IELTS"]
        )
    ]
    
    for material in materials:
        existing = ReadingMaterial.query.filter_by(title=material.title).first()
        if not existing:
            db.session.add(material)
    
    db.session.commit()
    print("✅ Additional reading materials added")

if __name__ == "__main__":
    # Use SQLite for development
    os.environ['DATABASE_URL'] = 'sqlite:///language_arts.db'
    
    app = create_app()
    with app.app_context():
        add_more_materials()
        
        # Print all materials
        all_materials = ReadingMaterial.query.all()
        print(f"\n📖 Total reading materials in database: {len(all_materials)}")
        for i, material in enumerate(all_materials, 1):
            print(f"{i}. '{material.title}' ({material.difficulty_level.title()}, {material.category.title()})")