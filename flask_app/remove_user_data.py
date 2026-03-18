from app import app
from models import db, UserWordStats

with app.app_context():
    UserWordStats.query.delete()
    db.session.commit()
    print("All user data removed.")