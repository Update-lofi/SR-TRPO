import pytest
from app import app, db, CardSet

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # БД в оперативной памяти для тестов
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
        with app.app_context():
            db.drop_all()

# 1. Тест главной страницы — код ответа 200
def test_index_200(client):
    rv = client.get('/')
    assert rv.status_code == 200

# 2. Тест добавления объекта — проверка, что объект появляется в БД
def test_add_set(client):
    rv = client.post('/set/add', data=dict(title='Тестовый набор', description='Описание'), follow_redirects=True)
    assert rv.status_code == 200
    with app.app_context():
        card_set = CardSet.query.filter_by(title='Тестовый набор').first()
        assert card_set is not None

# 3. Тест поиска/фильтрации — проверка, что возвращаются только нужные записи
def test_search_set(client):
    client.post('/set/add', data=dict(title='Английский', description='Words'))
    client.post('/set/add', data=dict(title='Математика', description='Formulas'))
    
    rv = client.get('/?search=Англ')
    
    # Декодируем байтовый ответ сервера в обычную текстовую строку (UTF-8)
    response_text = rv.data.decode('utf-8')
    
    # Ищем русские слова как обычные строки
    assert 'Английский' in response_text
    assert 'Математика' not in response_text

# 4. Тест обработки ошибки — 404 при обращении к несуществующему ID
def test_404_on_invalid_id(client):
    rv = client.get('/set/999')
    assert rv.status_code == 404

# 5. Тест на корректность данных — проверка валидации (отклоняет пустое поле title)
def test_validation_empty_field(client):
    rv = client.post('/set/add', data=dict(title='', description='Без названия'), follow_redirects=True)
    
    # Здесь тоже декодируем ответ, чтобы проверить русскую ошибку
    response_text = rv.data.decode('utf-8')
    assert 'Название обязательно!' in response_text
    
    with app.app_context():
        card_set = CardSet.query.first()
        assert card_set is None # В БД ничего не должно добавиться