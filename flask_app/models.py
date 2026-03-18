from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    stats = db.relationship('UserWordStats', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    words = db.relationship('Word', backref='lesson', lazy='dynamic')

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    latin = db.Column(db.String(128))
    german = db.Column(db.String(128))
    stats = db.relationship('UserWordStats', backref='word', lazy='dynamic')

class UserWordStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'))
    correct_count = db.Column(db.Integer, default=0)
    wrong_count = db.Column(db.Integer, default=0)
    last_reviewed = db.Column(db.DateTime, default=datetime.utcnow)
    last_attempts = db.Column(db.String(10), default="")
    streak = db.Column(db.Integer, default=0)
    negative_streak = db.Column(db.Integer, default=0)
    is_learned = db.Column(db.Boolean, default=False)
    times_reviewed = db.Column(db.Integer, default=0)
    times_shown = db.Column(db.Integer, default=0)
    next_review = db.Column(db.DateTime, default=datetime.utcnow)

    def add_attempt(self, is_correct):
        if self.correct_count is None: self.correct_count = 0
        if self.wrong_count is None: self.wrong_count = 0
        if self.streak is None: self.streak = 0
        if self.negative_streak is None: self.negative_streak = 0
        if self.last_attempts is None: self.last_attempts = ""
        if self.times_reviewed is None: self.times_reviewed = 0

        self.times_reviewed += 1

        if is_correct:
            self.correct_count += 1
            self.streak += 1
            self.negative_streak = 0
            if self.streak >= 3:
                self.is_learned = True
                self.next_review = datetime.utcnow() + timedelta(hours=24)
            result = "1"
        else:
            self.wrong_count += 1
            self.streak = 0
            self.negative_streak += 1
            self.is_learned = False
            self.next_review = datetime.utcnow()
            result = "0"
        
        self.last_reviewed = datetime.utcnow()
        self.last_attempts = (self.last_attempts + result)[-5:]

    @property
    def confidence(self):
        if self.streak == 0:
            return 0.0
        return 1.0 - (0.5 ** self.streak)

    @property
    def priority_tier(self):
        if not self.is_learned and self.streak > 0:
            return 1
        elif self.is_learned and self.negative_streak == 0:
            return 2
        elif self.is_learned and self.negative_streak > 0:
            return 1
        return 0

    @property
    def is_due(self):
        return datetime.utcnow() >= self.next_review

    @property
    def days_since_review(self):
        if not self.last_reviewed:
            return 999
        return (datetime.utcnow() - self.last_reviewed).days
