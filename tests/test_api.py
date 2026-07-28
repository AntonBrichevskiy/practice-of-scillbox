import pytest
import json
from datetime import datetime, timezone, timedelta
from app.models import Client, Parking, ClientParking
from tests.factories import ClientFactory, ParkingFactory, ClientParkingFactory


class TestAPI:
    """Тестирование API"""

    # ========== GET-методы ==========
    @pytest.mark.parametrize('endpoint', [
        '/clients',
        '/parkings',
        '/clients/1',
        '/parkings/1',
    ])
    def test_get_methods(self, client, test_client, test_parking, endpoint):
        """Проверка, что все GET-методы возвращают код 200"""
        response = client.get(endpoint)
        assert response.status_code == 200

    # ========== Создание клиента ==========
    def test_create_client(self, client):
        """Тест создания клиента"""
        data = {
            'name': 'Алексей',
            'surname': 'Смирнов',
            'credit_card': '1111-2222-3333-4444',
            'car_number': 'X789YZ'
        }
        response = client.post('/clients', json=data)
        assert response.status_code == 201
        assert response.json['name'] == 'Алексей'
        assert response.json['surname'] == 'Смирнов'
        assert response.json['credit_card'] == '1111-2222-3333-4444'
        assert response.json['car_number'] == 'X789YZ'

    def test_create_client_without_required_fields(self, client):
        """Тест создания клиента без обязательных полей"""
        data = {'name': 'Алексей'}  # Нет surname
        response = client.post('/clients', json=data)
        assert response.status_code == 400
        assert 'error' in response.json

    # ========== Создание парковки ==========
    def test_create_parking(self, client):
        """Тест создания парковки"""
        data = {
            'address': 'ул. Новая, д. 10',
            'count_places': 15
        }
        response = client.post('/parkings', json=data)
        assert response.status_code == 201
        assert response.json['address'] == 'ул. Новая, д. 10'
        assert response.json['count_places'] == 15
        assert response.json['count_available_places'] == 15
        assert response.json['opened'] == True

    def test_create_parking_without_required_fields(self, client):
        """Тест создания парковки без обязательных полей"""
        data = {'address': 'ул. Новая, д. 10'}  # Нет count_places
        response = client.post('/parkings', json=data)
        assert response.status_code == 400
        assert 'error' in response.json

    # ========== Заезд на парковку ==========
    @pytest.mark.parking
    def test_parking_entry(self, client, db_session):
        """Тест заезда на парковку"""
        from datetime import datetime, timezone, timedelta

        # Создаём клиента и парковку через фабрики
        test_client = ClientFactory()
        test_parking = ParkingFactory(count_places=3, opened=True)

        # Убедимся, что места доступны (на всякий случай)
        test_parking.count_available_places = 3
        db_session.commit()

        # Проверяем, что места доступны
        assert test_parking.count_available_places == 3

        # Выполняем заезд
        data = {
            'client_id': test_client.id,
            'parking_id': test_parking.id
        }
        response = client.post('/client_parkings', json=data)

        # Проверяем ответ
        assert response.status_code == 201
        assert response.json['time_in'] is not None
        assert response.json['time_out'] is None

        # Проверяем, что количество мест уменьшилось
        assert response.json['parking']['count_available_places'] == 2

    @pytest.mark.parking
    def test_parking_entry_already_parked(self, client, test_client_parking):
        """Тест повторного заезда на ту же парковку"""
        data = {
            'client_id': test_client_parking.client_id,
            'parking_id': test_client_parking.parking_id
        }
        response = client.post('/client_parkings', json=data)
        assert response.status_code == 400
        assert 'Client already parked' in response.json['error']

    @pytest.mark.parking
    def test_parking_entry_closed(self, client, test_client, test_parking_closed):
        """Тест заезда на закрытую парковку"""
        data = {
            'client_id': test_client.id,
            'parking_id': test_parking_closed.id
        }
        response = client.post('/client_parkings', json=data)
        assert response.status_code == 400
        assert 'Parking is closed' in response.json['error']

    @pytest.mark.parking
    def test_parking_entry_no_places(self, client, db_session):
        """Тест заезда на заполненную парковку"""
        test_client = ClientFactory()
        test_parking = ParkingFactory(count_places=1, count_available_places=0, opened=True)
        db_session.commit()

        data = {
            'client_id': test_client.id,
            'parking_id': test_parking.id
        }
        response = client.post('/client_parkings', json=data)
        assert response.status_code == 400
        assert 'No available places' in response.json['error']

    @pytest.mark.parking
    def test_parking_entry_invalid_client(self, client, test_parking):
        """Тест заезда с несуществующим клиентом"""
        data = {
            'client_id': 999,
            'parking_id': test_parking.id
        }
        response = client.post('/client_parkings', json=data)
        assert response.status_code == 404
        assert 'Client not found' in response.json['error']

    @pytest.mark.parking
    def test_parking_entry_invalid_parking(self, client, test_client):
        """Тест заезда на несуществующую парковку"""
        data = {
            'client_id': test_client.id,
            'parking_id': 999
        }
        response = client.post('/client_parkings', json=data)
        assert response.status_code == 404
        assert 'Parking not found' in response.json['error']

    # ========== Выезд с парковки ==========
    @pytest.mark.parking
    def test_parking_exit(self, client, db_session):
        """Тест выезда с парковки (клиент с картой)"""
        from datetime import datetime, timezone, timedelta

        # Создаём клиента с картой и открытую парковку
        test_client = ClientFactory(credit_card='1234-5678-9012-3456')
        test_parking = ParkingFactory(count_places=3, opened=True)
        test_parking.count_available_places = 3
        db_session.commit()

        # Создаём запись о парковке
        client_parking = ClientParkingFactory(
            client=test_client,
            parking=test_parking,
            time_in=datetime.now(timezone.utc) - timedelta(hours=1),
            time_out=None
        )

        data = {
            'client_id': test_client.id,
            'parking_id': test_parking.id
        }
        response = client.delete('/client_parkings', json=data)

        # Если ошибка — печатаем для отладки
        if response.status_code != 200:
            print(f"Ошибка: {response.status_code} - {response.json}")

        assert response.status_code == 200
        assert response.json['time_out'] is not None
        assert response.json['time_out'] > response.json['time_in']

    @pytest.mark.parking
    def test_parking_exit_no_card(self, client, db_session):
        """Тест выезда клиента без карты"""
        from datetime import datetime, timezone, timedelta

        # Создаём клиента без карты и открытую парковку
        test_client = ClientFactory(credit_card=None)
        test_parking = ParkingFactory(count_places=3, opened=True)
        test_parking.count_available_places = 3
        db_session.commit()

        # Создаём запись о парковке
        client_parking = ClientParkingFactory(
            client=test_client,
            parking=test_parking,
            time_in=datetime.now(timezone.utc) - timedelta(hours=1),
            time_out=None
        )

        data = {
            'client_id': test_client.id,
            'parking_id': test_parking.id
        }
        response = client.delete('/client_parkings', json=data)
        assert response.status_code == 400
        assert 'Client has no credit card' in response.json['error']

    @pytest.mark.parking
    def test_parking_exit_not_parked(self, client, db_session):
        """Тест выезда клиента, который не на парковке"""
        # Создаём клиента и парковку, но НЕ создаём запись о парковке
        test_client = ClientFactory()
        test_parking = ParkingFactory(count_places=3, opened=True)
        db_session.commit()

        data = {
            'client_id': test_client.id,
            'parking_id': test_parking.id
        }
        response = client.delete('/client_parkings', json=data)
        assert response.status_code == 404
        assert 'Client not parked' in response.json['error']

    @pytest.mark.parking
    def test_parking_exit_updates_places(self, client, db_session):
        """Тест, что при выезде количество мест увеличивается"""
        from datetime import datetime, timezone, timedelta

        # Создаём клиента с картой и открытую парковку
        test_client = ClientFactory(credit_card='1234-5678-9012-3456')
        test_parking = ParkingFactory(count_places=3, opened=True)
        test_parking.count_available_places = 3
        db_session.commit()

        # Создаём запись о парковке
        client_parking = ClientParkingFactory(
            client=test_client,
            parking=test_parking,
            time_in=datetime.now(timezone.utc) - timedelta(hours=1),
            time_out=None
        )

        # Уменьшаем количество мест (как будто машина уже на парковке)
        test_parking.count_available_places -= 1
        db_session.commit()

        # Проверяем количество мест до выезда
        response = client.get('/parkings')
        assert response.status_code == 200
        parkings = response.json
        parking_before = next(p for p in parkings if p['id'] == test_parking.id)
        places_before = parking_before['count_available_places']

        # Выезжаем
        data = {
            'client_id': test_client.id,
            'parking_id': test_parking.id
        }
        response = client.delete('/client_parkings', json=data)
        assert response.status_code == 200

        # Проверяем количество мест после выезда
        response = client.get('/parkings')
        assert response.status_code == 200
        parkings = response.json
        parking_after = next(p for p in parkings if p['id'] == test_parking.id)
        places_after = parking_after['count_available_places']

        assert places_after == places_before + 1

    # ========== Тест времени ==========
    @pytest.mark.parking
    def test_parking_time_validation(self, client, db_session):
        """Тест, что время выезда не может быть меньше времени заезда"""
        # Создаём клиента с картой и открытую парковку
        test_client = ClientFactory(credit_card='1234-5678-9012-3456')  # Явно указываем карту
        test_parking = ParkingFactory(count_places=3, opened=True)
        test_parking.count_available_places = 3
        db_session.commit()

        # Создаём запись о заезде (1 час назад)
        time_in = datetime.now(timezone.utc) - timedelta(hours=1)
        client_parking = ClientParkingFactory(
            client=test_client,
            parking=test_parking,
            time_in=time_in,
            time_out=None
        )

        # Убеждаемся, что парковка всё ещё открыта
        test_parking.opened = True
        db_session.commit()

        # Выезжаем
        data = {
            'client_id': test_client.id,
            'parking_id': test_parking.id
        }
        response = client.delete('/client_parkings', json=data)

        # Если ошибка — печатаем для отладки
        if response.status_code != 200:
            print(f"Ошибка: {response.status_code} - {response.json}")

        assert response.status_code == 200
        assert response.json['time_out'] is not None
        assert response.json['time_out'] > response.json['time_in']

    # ========== Дополнительный тест ==========
    def test_get_client_by_id(self, client, test_client):
        """Тест получения клиента по ID"""
        response = client.get(f'/clients/{test_client.id}')
        assert response.status_code == 200
        assert response.json['id'] == test_client.id
        assert response.json['name'] == test_client.name

    def test_get_parking_by_id(self, client, test_parking):
        """Тест получения парковки по ID"""
        response = client.get(f'/parkings/{test_parking.id}')
        assert response.status_code == 200
        assert response.json['id'] == test_parking.id
        assert response.json['address'] == test_parking.address

    # ==========ТЕСТЫ С ИСПОЛЬЗОВАНИЕМ ФАБРИК ==========

    def test_create_client_with_factory(self, client, db_session):
        """Тест создания клиента с использованием ClientFactory"""
        # Создаём данные клиента через фабрику (build() — не сохраняет в БД)
        client_data = ClientFactory.build()

        # Запоминаем количество клиентов ДО запроса
        count_before = Client.query.count()

        # Отправляем запрос на создание клиента через API
        data = {
            'name': client_data.name,
            'surname': client_data.surname,
            'credit_card': client_data.credit_card,
            'car_number': client_data.car_number
        }
        response = client.post('/clients', json=data)

        # Проверяем ответ API
        assert response.status_code == 201
        assert response.json['name'] == client_data.name
        assert response.json['surname'] == client_data.surname
        assert response.json['credit_card'] == client_data.credit_card
        assert response.json['car_number'] == client_data.car_number

        # Проверяем, что клиент создался в БД (количество увеличилось на 1)
        count_after = Client.query.count()
        assert count_after == count_before + 1

    def test_create_parking_with_factory(self, client, db_session):
        """Тест создания парковки с использованием ParkingFactory"""
        # Создаём данные парковки через фабрику (build() — не сохраняет в БД)
        parking_data = ParkingFactory.build()

        # Запоминаем количество парковок ДО запроса
        count_before = Parking.query.count()

        # Отправляем запрос на создание парковки через API
        data = {
            'address': parking_data.address,
            'count_places': parking_data.count_places,
            'opened': parking_data.opened
        }
        response = client.post('/parkings', json=data)

        # Проверяем ответ API
        assert response.status_code == 201
        assert response.json['address'] == parking_data.address
        assert response.json['count_places'] == parking_data.count_places
        assert response.json['opened'] == parking_data.opened
        assert response.json['count_available_places'] == parking_data.count_places

        # Проверяем, что парковка создалась в БД (количество увеличилось на 1)
        count_after = Parking.query.count()
        assert count_after == count_before + 1
