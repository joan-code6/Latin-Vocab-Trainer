from app import app, db
from models import Lesson, Word

with app.app_context():
    # Delete L20 and all its words
    l20 = Lesson.query.filter_by(name='L20').first()
    if l20:
        Word.query.filter_by(lesson_id=l20.id).delete()
        db.session.delete(l20)
        db.session.commit()
        print("Deleted L20 and all its words. Visit /import_data to re-import it.")
    else:
        print("L20 not found")
