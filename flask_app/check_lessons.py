from app import app, db
from models import Lesson

with app.app_context():
    lessons = Lesson.query.all()
    print([l.name for l in lessons])