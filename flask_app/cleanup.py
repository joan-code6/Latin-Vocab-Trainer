from app import app, db
from models import Lesson, Word
from sqlalchemy import func

with app.app_context():
    # Delete lessons matching 'Lektion%' pattern
    lessons_to_delete = Lesson.query.filter(Lesson.name.like('Lektion%')).all()
    for lesson in lessons_to_delete:
        db.session.delete(lesson)
    db.session.commit()
    print(f"Deleted {len(lessons_to_delete)} duplicate lessons")
    
    # Find and remove duplicate words within each lesson
    lessons = Lesson.query.all()
    total_removed = 0
    
    for lesson in lessons:
        # Get all words for this lesson grouped by latin text
        words = Word.query.filter_by(lesson_id=lesson.id).all()
        
        # Track seen latin words
        seen = {}
        duplicates = []
        
        for word in words:
            key = (word.latin.lower().strip(), word.german.lower().strip())
            if key in seen:
                # This is a duplicate
                duplicates.append(word)
            else:
                seen[key] = word
        
        # Delete duplicates
        for dup in duplicates:
            db.session.delete(dup)
            total_removed += 1
        
    db.session.commit()
    print(f"Removed {total_removed} duplicate words")
    print("Cleanup complete!")