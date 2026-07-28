import pytest
from datetime import datetime, timezone, timedelta
from app import create_app
from app.models import db, Client, Parking, ClientParking
from tests.factories import ClientFactory, ParkingFactory, ClientParkingFactory


@pytest.fixture(scope='session')
def app():
    """Создание тестового приложения"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Клиент для запросов к приложению"""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Сессия БД для тестов"""
    with app.app_context():
        yield db.session
        db.session.rollback()
        db.session.remove()


@pytest.fixture
def test_client(db_session):
    """Создание тестового клиента через фабрику (может быть без карты)"""
    client = ClientFactory()
    return client


@pytest.fixture
def test_client_with_card(db_session):  # <-- НОВАЯ ФИКСТУРА
    """Создание тестового клиента с картой"""
    client = ClientFactory(credit_card='1234-5678-9012-3456')
    return client


@pytest.fixture
def test_client_no_card(db_session):
    """Создание тестового клиента без карты через фабрику"""
    client = ClientFactory(credit_card=None)
    return client


@pytest.fixture
def test_parking(db_session):
    """Создание тестовой парковки через фабрику"""
    parking = ParkingFactory(count_places=3, opened=True)
    parking.count_available_places = 3
    db_session.commit()
    return parking

@pytest.fixture
def test_parking_closed(db_session):
    """Создание закрытой парковки через фабрику"""
    parking = ParkingFactory(opened=False, count_places=5)
    return parking

@pytest.fixture
def test_parking_full(db_session):
    """Создание заполненной парковки через фабрику"""
    parking = ParkingFactory(
        count_places=1,
        count_available_places=0,
        opened=True
    )
    return parking


@pytest.fixture
def test_client_parking(db_session, test_client, test_parking):
    """Создание записи о парковке через фабрику (для клиента без гарантированной карты)"""
    test_parking.count_available_places -= 1
    db_session.commit()

    client_parking = ClientParkingFactory(
        client=test_client,
        parking=test_parking,
        time_in=datetime.now(timezone.utc) - timedelta(hours=1),
        time_out=None
    )
    return client_parking


@pytest.fixture
def test_client_parking_with_exit(db_session, test_client, test_parking):
    """Создание записи о парковке с выездом"""
    test_parking.count_available_places -= 1
    db_session.commit()

    time_in = datetime.now(timezone.utc) - timedelta(hours=2)
    time_out = datetime.now(timezone.utc) - timedelta(hours=1)

    client_parking = ClientParkingFactory(
        client=test_client,
        parking=test_parking,
        time_in=time_in,
        time_out=time_out
    )
    return client_parking
