from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
from datetime import datetime, timedelta
import json
import os
import random

try:
    from .app import app, db
    from .models import User, Lesson, Word, UserWordStats
except ImportError:
    from app import app, db
    from models import User, Lesson, Word, UserWordStats

LEARNING_POOL_SIZE = 6
STREAK_TO_LEARN = 3

@app.route('/')
@login_required
def index():
    lessons = Lesson.query.all()
    return render_template('index.html', lessons=lessons)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/api/get_next_word', methods=['POST'])
@login_required
def get_next_word():
    data = request.get_json() or {}
    lesson_ids = data.get('lessons', [])
    last_word_id = data.get('last_word_id', None)
    
    if not lesson_ids:
        return jsonify({'error': 'No lessons selected'}), 400

    words = Word.query.filter(Word.lesson_id.in_(lesson_ids)).all()
    
    word_stats = {}
    for word in words:
        stats = UserWordStats.query.filter_by(user_id=current_user.id, word_id=word.id).first()
        word_stats[word.id] = {
            'word': word,
            'stats': stats,
            'streak': stats.streak if stats else 0,
            'negative_streak': stats.negative_streak if stats else 0,
            'confidence': stats.confidence if stats else 0.0
        }
    
    learning_pool = []
    rest_pool = []
    learned_pool = []
    mastered_pool = []
    
    for word_id, data in word_stats.items():
        streak = data['streak']
        neg_streak = data['negative_streak']
        
        if streak >= 5:
            mastered_pool.append(data)
        elif streak >= 3:
            learned_pool.append(data)
        elif neg_streak > 0 or (streak > 0 and streak < 3):
            learning_pool.append(data)
        else:
            rest_pool.append(data)
    
    if len(learning_pool) < LEARNING_POOL_SIZE:
        rest_pool.sort(key=lambda x: x['confidence'])
        needed = LEARNING_POOL_SIZE - len(learning_pool)
        for i in range(min(needed, len(rest_pool))):
            learning_pool.append(rest_pool.pop(0))
    
    learning_pool.sort(key=lambda x: (x['negative_streak'] > 0, x['confidence']))
    
    chosen_word = None
    tier_source = 'rest'
    
    roll = random.random()
    
    if learning_pool and roll < 0.60:
        random.shuffle(learning_pool)
        chosen_word = learning_pool[0]
        tier_source = 'learning'
    elif roll < 0.90:
        if rest_pool:
            for w in sorted(rest_pool, key=lambda x: x['confidence']):
                if w['word'].id != last_word_id:
                    chosen_word = w
                    break
            if not chosen_word:
                chosen_word = random.choice(rest_pool)
            tier_source = 'rest'
        else:
            roll = 0.70
    elif roll < 0.98:
        if learned_pool:
            for w in sorted(learned_pool, key=lambda x: x['stats'].days_since_review if x['stats'] else 999, reverse=True):
                if w['word'].id != last_word_id:
                    chosen_word = w
                    break
            if not chosen_word and learned_pool:
                chosen_word = random.choice(learned_pool)
            tier_source = 'learned'
        else:
            roll = 0.92
    else:
        if mastered_pool:
            chosen_word = random.choice(mastered_pool)
            tier_source = 'mastered'
        else:
            roll = 0.50
    
    if not chosen_word:
        if learning_pool:
            chosen_word = random.choice(learning_pool)
            tier_source = 'learning'
        elif rest_pool:
            chosen_word = random.choice(rest_pool)
            tier_source = 'rest'
        elif learned_pool:
            chosen_word = random.choice(learned_pool)
            tier_source = 'learned'
        elif mastered_pool:
            chosen_word = random.choice(mastered_pool)
            tier_source = 'mastered'
        else:
            return jsonify({'error': 'No words available'}), 400
    
    word_obj = chosen_word['word']
    stats_obj = chosen_word['stats']
    
    if not stats_obj:
        stats_obj = UserWordStats(user_id=current_user.id, word_id=word_obj.id)
        db.session.add(stats_obj)
        db.session.commit()
    
    if stats_obj.times_shown is None:
        stats_obj.times_shown = 0
    stats_obj.times_shown += 1
    db.session.commit()
    
    return jsonify({
        'id': word_obj.id,
        'latin': word_obj.latin,
        'german': word_obj.german,
        'streak': chosen_word['streak'],
        'tier': tier_source,
        'confidence': chosen_word['confidence'],
        'is_learned': chosen_word['streak'] >= STREAK_TO_LEARN,
        'learning_pool_size': len(learning_pool),
        'rest_pool_size': len(rest_pool),
        'mastered_count': len(mastered_pool),
        'learned_count': len(learned_pool)
    })

@app.route('/api/submit_result', methods=['POST'])
@login_required
def submit_result():
    data = request.get_json() or {}
    word_id = data.get('word_id')
    is_correct = data.get('correct')
    
    stats = UserWordStats.query.filter_by(user_id=current_user.id, word_id=word_id).first()
    if not stats:
        stats = UserWordStats(user_id=current_user.id, word_id=word_id)
        db.session.add(stats)
    
    was_learned = stats.is_learned
    old_streak = stats.streak
    
    stats.add_attempt(is_correct)
    db.session.commit()
    
    just_learned = False
    if is_correct and stats.streak >= STREAK_TO_LEARN and not was_learned:
        just_learned = True
    
    demoted = False
    if was_learned and not is_correct:
        demoted = True
    
    words = Word.query.get(word_id)
    lesson_stats = None
    if words:
        lesson_words = Word.query.filter_by(lesson_id=words.lesson_id).all()
        total = len(lesson_words)
        learned = 0
        for w in lesson_words:
            s = UserWordStats.query.filter_by(user_id=current_user.id, word_id=w.id).first()
            if s and s.is_learned:
                learned += 1
        lesson_stats = {
            'learned': learned,
            'total': total,
            'percent': round((learned / total) * 100) if total > 0 else 0
        }
    
    return jsonify({
        'status': 'success',
        'confidence': stats.confidence,
        'streak': stats.streak,
        'is_learned': stats.is_learned,
        'just_learned': just_learned,
        'demoted': demoted,
        'tier_change': 'learned' if just_learned else ('learning' if demoted else None),
        'lesson_progress': lesson_stats
    })

@app.route('/api/get_learning_status', methods=['POST'])
@login_required
def get_learning_status():
    data = request.get_json() or {}
    lesson_ids = data.get('lessons', [])
    
    if not lesson_ids:
        return jsonify({})
    
    words = Word.query.filter(Word.lesson_id.in_(lesson_ids)).all()
    
    total = len(words)
    learning = 0
    learned = 0
    mastered = 0
    rest = 0
    
    learning_words = []
    
    for word in words:
        stats = UserWordStats.query.filter_by(user_id=current_user.id, word_id=word.id).first()
        
        if not stats:
            rest += 1
            continue
        
        if stats.streak >= 5:
            mastered += 1
        elif stats.streak >= 3:
            learned += 1
        elif stats.negative_streak > 0 or (stats.streak > 0 and stats.streak < 3):
            learning += 1
            if len(learning_words) < 6:
                learning_words.append({
                    'latin': word.latin,
                    'streak': stats.streak,
                    'is_demoted': stats.negative_streak > 0
                })
        else:
            rest += 1
    
    return jsonify({
        'total': total,
        'rest': rest,
        'learning': learning,
        'learned': learned,
        'mastered': mastered,
        'learning_words': learning_words,
        'overall_progress': round(((learned + mastered) / total) * 100) if total > 0 else 0
    })

@app.route('/api/get_progress', methods=['POST'])
@login_required
def get_progress():
    data = request.get_json() or {}
    lesson_ids = data.get('lessons', [])
    
    if not lesson_ids:
        return jsonify({'progress': 0.0})
    
    words = Word.query.filter(Word.lesson_id.in_(lesson_ids)).all()
    
    if not words:
        return jsonify({'progress': 0.0})
    
    total_confidence = 0.0
    learned_count = 0
    for word in words:
        stats = UserWordStats.query.filter_by(user_id=current_user.id, word_id=word.id).first()
        if stats:
            total_confidence += stats.confidence
            if stats.is_learned:
                learned_count += 1
    
    return jsonify({
        'progress': learned_count / len(words),
        'learned_count': learned_count,
        'total_count': len(words)
    })

@app.route('/api/get_progress_breakdown', methods=['POST'])
@login_required
def get_progress_breakdown():
    data = request.get_json() or {}
    lesson_ids = data.get('lessons', [])
    
    if not lesson_ids:
        return jsonify([])
    
    result = []
    for lesson_id in lesson_ids:
        lesson = Lesson.query.get(lesson_id)
        if not lesson:
            continue
        
        words = Word.query.filter_by(lesson_id=lesson_id).all()
        if not words:
            continue
        
        total = len(words)
        learned = 0
        mastered = 0
        learning = 0
        new_count = 0
        
        for word in words:
            stats = UserWordStats.query.filter_by(user_id=current_user.id, word_id=word.id).first()
            if not stats:
                new_count += 1
            elif stats.streak >= 5:
                mastered += 1
                learned += 1
            elif stats.is_learned:
                learned += 1
            elif stats.streak > 0:
                learning += 1
            else:
                new_count += 1
        
        result.append({
            'lesson_id': lesson_id,
            'lesson_name': lesson.name,
            'progress': learned / total if total > 0 else 0.0,
            'total': total,
            'learned': learned,
            'mastered': mastered,
            'learning': learning,
            'new': new_count
        })
    
    return jsonify(result)

@app.route('/stats')
@login_required
def stats():
    lessons = Lesson.query.all()
    return render_template('stats.html', lessons=lessons)

@app.route('/import_data')
@login_required
def import_data():
    base_path = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(base_path)

    imported_count = 0
    missing_files = []
    import_errors = []

    lesson_files = []
    index_path = os.path.join(workspace_root, 'index.json')
    if os.path.exists(index_path):
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                lessons_data = json.load(f)
            for lesson_info in lessons_data:
                path = lesson_info.get('path')
                if isinstance(path, str) and path.endswith('.json'):
                    lesson_files.append(path)
        except Exception as e:
            import_errors.append(f"index.json: {e}")

    for filename in os.listdir(workspace_root):
        if filename.startswith('L') and filename.endswith('.json') and 'LT' not in filename:
            lesson_files.append(filename)

    for filename in sorted(set(lesson_files)):
        lesson_path = os.path.join(workspace_root, filename)
        if not os.path.exists(lesson_path):
            missing_files.append(filename)
            continue

        lesson_name = os.path.splitext(os.path.basename(filename))[0]

        lesson = Lesson.query.filter_by(name=lesson_name).first()
        if not lesson:
            lesson = Lesson(name=lesson_name)
            db.session.add(lesson)
            db.session.commit()

        try:
            with open(lesson_path, 'r', encoding='utf-8') as f:
                words_data = json.load(f)

            for w in words_data:
                latin = w.get('latein')
                german = w.get('deutsch')
                if not latin or not german:
                    continue

                existing_word = Word.query.filter_by(lesson_id=lesson.id, latin=latin).first()
                if not existing_word:
                    new_word = Word(lesson_id=lesson.id, latin=latin, german=german)
                    db.session.add(new_word)
                    imported_count += 1

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            import_errors.append(f"{filename}: {e}")

    message = f"Imported {imported_count} words successfully."
    if missing_files:
        message += f" Missing files: {', '.join(missing_files)}."
    if import_errors:
        message += f" Import errors: {' | '.join(import_errors[:3])}."

    flash(message)
    return redirect(url_for('index'))
