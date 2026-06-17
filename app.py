from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-dev'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Модели БД ---
class CardSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    cards = db.relationship('Card', backref='card_set', lazy=True, cascade="all, delete-orphan")

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    set_id = db.Column(db.Integer, db.ForeignKey('card_set.id'), nullable=False)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.String(255), nullable=False)

# Создание таблиц
with app.app_context():
    db.create_all()

# --- Маршруты ---
@app.route('/')
def index():
    search_query = request.args.get('search', '')
    if search_query:
        sets = CardSet.query.filter(CardSet.title.contains(search_query)).all()
    else:
        sets = CardSet.query.all()
    return render_template('index.html', sets=sets, search_query=search_query)

@app.route('/set/add', methods=['GET', 'POST'])
def add_set():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        if not title:
            flash('Название обязательно!', 'danger')
            return redirect(url_for('add_set'))
        new_set = CardSet(title=title, description=description)
        db.session.add(new_set)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_set.html')

@app.route('/set/<int:set_id>')
def set_detail(set_id):
    card_set = CardSet.query.get_or_404(set_id)
    return render_template('set_detail.html', card_set=card_set)

@app.route('/set/<int:set_id>/card/add', methods=['POST'])
def add_card(set_id):
    card_set = CardSet.query.get_or_404(set_id)
    question = request.form.get('question')
    answer = request.form.get('answer')
    if question and answer:
        new_card = Card(set_id=card_set.id, question=question, answer=answer)
        db.session.add(new_card)
        db.session.commit()
    return redirect(url_for('set_detail', set_id=set_id))

@app.route('/set/<int:set_id>/train', methods=['GET', 'POST'])
def train(set_id):
    card_set = CardSet.query.get_or_404(set_id)
    if not card_set.cards:
        flash('В этом наборе нет карточек для тренировки.', 'warning')
        return redirect(url_for('set_detail', set_id=set_id))
    
    if request.method == 'POST':
        correct_count = 0
        total = len(card_set.cards)
        for card in card_set.cards:
            user_answer = request.form.get(f'answer_{card.id}', '').strip().lower()
            if user_answer == card.answer.strip().lower():
                correct_count += 1
        
        score = int((correct_count / total) * 100)
        return render_template('train_result.html', card_set=card_set, score=score, correct=correct_count, total=total)

    # Перемешиваем карточки для тренировки
    cards = list(card_set.cards)
    random.shuffle(cards)
    return render_template('train.html', card_set=card_set, cards=cards)

if __name__ == '__main__':
    app.run(debug=True)