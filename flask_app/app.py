from flask import Flask
from config import Config
from models import db, User, Lesson, Word
from flask_login import LoginManager
import json
import os

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login = LoginManager(app)
login.login_view = 'login'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

from routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        index_path = os.path.join(workspace_root, 'index.json')
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                lessons_data = json.load(f)
            for lesson_info in lessons_data:
                lesson_name = lesson_info['path'].replace('.json', '')
                lesson_path = lesson_info['path']
                lesson_file = os.path.join(workspace_root, lesson_path)
                if os.path.exists(lesson_file):
                    lesson = Lesson.query.filter_by(name=lesson_name).first()
                    if not lesson:
                        lesson = Lesson(name=lesson_name)
                        db.session.add(lesson)
                        db.session.commit()
                    with open(lesson_file, 'r', encoding='utf-8') as f:
                        words_data = json.load(f)
                    for w in words_data:
                        existing_word = Word.query.filter_by(lesson_id=lesson.id, latin=w['latein']).first()
                        if not existing_word:
                            new_word = Word(lesson_id=lesson.id, latin=w['latein'], german=w['deutsch'])
                            db.session.add(new_word)
                    db.session.commit()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
