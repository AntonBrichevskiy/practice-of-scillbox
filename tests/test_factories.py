import pytest
from app.models import Client, Parking, ClientParking
from tests.factories import ClientFactory, ParkingFactory, ClientParkingFactory


class TestFactories:

    def test_client_factory_creates_client(self, db_session):
        initial_count = Client.query.count()
        client = ClientFactory()

        assert client.id is not None
        assert client.name is not None
        assert client.surname is not None
        assert isinstance(client.credit_card, (str, type(None)))
        assert client.car_number is not None
        assert Client.query.count() == initial_count + 1

    def test_client_factory_without_card(self, db_session):
        client = ClientFactory(credit_card=None)
        assert client.id is not None
        assert client.credit_card is None

    def test_parking_factory_creates_parking(self, db_session):
        initial_count = Parking.query.count()
        parking = ParkingFactory()

        assert parking.id is not None
        assert parking.address is not None
        assert isinstance(parking.opened, bool)
        assert parking.count_places >= 5
        assert parking.count_available_places == parking.count_places
        assert Parking.query.count() == initial_count + 1

    def test_parking_factory_closed(self, db_session):
        parking = ParkingFactory(opened=False)
        assert parking.opened == False

    def test_client_parking_factory(self, db_session):
        client = ClientFactory()
        parking = ParkingFactory()

        client_parking = ClientParkingFactory(
            client=client,
            parking=parking,
            time_out=None
        )

        assert client_parking.id is not None
        assert client_parking.client_id == client.id
        assert client_parking.parking_id == parking.id
        assert client_parking.time_in is not None
        assert client_parking.time_out is None

    def test_client_parking_with_exit(self, db_session):
        client = ClientFactory()
        parking = ParkingFactory()

        client_parking = ClientParkingFactory(
            client=client,
            parking=parking,
            time_out=None
        )

        if client_parking.time_out:
            assert client_parking.time_out > client_parking.time_in

    def test_factory_batch_creation(self, db_session):
        clients = ClientFactory.create_batch(5)
        assert len(clients) == 5
        assert Client.query.count() >= 5

        parkings = ParkingFactory.create_batch(3)
        assert len(parkings) == 3
        assert Parking.query.count() >= 3