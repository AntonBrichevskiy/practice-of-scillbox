import factory
from factory import Faker, LazyAttribute, SubFactory
from factory.alchemy import SQLAlchemyModelFactory
from app.models import db, Client, Parking, ClientParking
from datetime import datetime, timedelta
import random


class ClientFactory(SQLAlchemyModelFactory):
    """Фабрика для создания клиентов"""

    class Meta:
        model = Client
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'

    name = Faker('first_name')
    surname = Faker('last_name')
    credit_card = factory.Maybe(
        factory.Faker('boolean', chance_of_getting_true=70),
        yes_declaration=Faker('credit_card_number'),
        no_declaration=None
    )
    car_number = Faker('bothify', text='??#####')


class ParkingFactory(SQLAlchemyModelFactory):
    """Фабрика для создания парковок"""

    class Meta:
        model = Parking
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'

    address = Faker('street_address')
    opened = Faker('boolean', chance_of_getting_true=80)
    count_places = Faker('random_int', min=5, max=50)

    @LazyAttribute
    def count_available_places(self):
        return self.count_places


class ClientParkingFactory(SQLAlchemyModelFactory):
    """Фабрика для создания записей о парковке"""

    class Meta:
        model = ClientParking
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'

    client = SubFactory(ClientFactory)
    parking = SubFactory(ParkingFactory)
    time_in = Faker('date_time_this_year', before_now=True, after_now=False)
    time_out = None


class ClientParkingWithExitFactory(ClientParkingFactory):
    """Фабрика для записей о парковке с выездом"""
    time_out = factory.LazyAttribute(
        lambda o: o.time_in + timedelta(hours=random.randint(1, 5))
    )