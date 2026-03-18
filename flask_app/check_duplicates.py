from app import app, db
from models import Lesson, Word
from sqlalchemy import func

with app.app_context():
    # Show all lessons and their word counts
    lessons = Lesson.query.all()
    
    print("\n=== Lesson Overview ===")
    for lesson in lessons:
        word_count = Word.query.filter_by(lesson_id=lesson.id).count()
        print(f"{lesson.name}: {word_count} words")
    
    # For L20, show if there are any duplicates
    l20 = Lesson.query.filter_by(name='L20').first()
    if l20:
        print(f"\n=== L20 Words (showing first 20) ===")
        words = Word.query.filter_by(lesson_id=l20.id).limit(20).all()
        for w in words:
            print(f"  {w.id}: {w.latin} = {w.german}")
        
        # Check for exact duplicates
        print(f"\n=== Checking for duplicates in L20 ===")
        all_words = Word.query.filter_by(lesson_id=l20.id).all()
        seen = {}
        for w in all_words:
            key = (w.latin, w.german)
            if key in seen:
                print(f"DUPLICATE: ID {w.id} = {w.latin} / {w.german} (original ID: {seen[key]})")
            else:
                seen[key] = w.id
