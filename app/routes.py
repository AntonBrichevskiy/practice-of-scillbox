from flask import jsonify, request
from .models import db, Client, Parking, ClientParking
from datetime import datetime, timezone


def init_routes(app):
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'})

    # ========== КЛИЕНТЫ ==========
    @app.route('/clients', methods=['GET'])
    def get_clients():
        clients = Client.query.all()
        return jsonify([c.to_json() for c in clients])

    @app.route('/clients/<int:client_id>', methods=['GET'])  # <-- ДОБАВЛЕНО
    def get_client(client_id):
        client = Client.query.get_or_404(client_id)
        return jsonify(client.to_json())

    @app.route('/clients', methods=['POST'])
    def create_client():
        data = request.get_json()
        if not data or 'name' not in data or 'surname' not in data:
            return jsonify({'error': 'Name and surname are required'}), 400

        client = Client(
            name=data['name'],
            surname=data['surname'],
            credit_card=data.get('credit_card'),
            car_number=data.get('car_number')
        )
        db.session.add(client)
        db.session.commit()
        return jsonify(client.to_json()), 201

    # ========== ПАРКОВКИ ==========
    @app.route('/parkings', methods=['GET'])
    def get_parkings():
        parkings = Parking.query.all()
        return jsonify([p.to_json() for p in parkings])

    @app.route('/parkings/<int:parking_id>', methods=['GET'])  # <-- ДОБАВЛЕНО
    def get_parking(parking_id):
        parking = Parking.query.get_or_404(parking_id)
        return jsonify(parking.to_json())

    @app.route('/parkings', methods=['POST'])
    def create_parking():
        data = request.get_json()
        if not data or 'address' not in data or 'count_places' not in data:
            return jsonify({'error': 'Address and count_places are required'}), 400

        parking = Parking(
            address=data['address'],
            opened=data.get('opened', True),
            count_places=data['count_places'],
            count_available_places=data['count_places']
        )
        db.session.add(parking)
        db.session.commit()
        return jsonify(parking.to_json()), 201

    # ========== ЗАЕЗД/ВЫЕЗД ==========
    @app.route('/client_parkings', methods=['POST'])
    def create_client_parking():
        data = request.get_json()
        if not data or 'client_id' not in data or 'parking_id' not in data:
            return jsonify({'error': 'client_id and parking_id are required'}), 400

        client = Client.query.get(data['client_id'])
        parking = Parking.query.get(data['parking_id'])

        if not client:
            return jsonify({'error': 'Client not found'}), 404
        if not parking:
            return jsonify({'error': 'Parking not found'}), 404
        if not parking.opened:
            return jsonify({'error': 'Parking is closed'}), 400
        if parking.count_available_places <= 0:
            return jsonify({'error': 'No available places'}), 400

        existing = ClientParking.query.filter_by(
            client_id=data['client_id'],
            parking_id=data['parking_id'],
            time_out=None
        ).first()

        if existing:
            return jsonify({'error': 'Client already parked at this parking'}), 400

        client_parking = ClientParking(
            client_id=data['client_id'],
            parking_id=data['parking_id'],
            time_in=datetime.utcnow()
        )
        parking.count_available_places -= 1

        db.session.add(client_parking)
        db.session.commit()
        return jsonify(client_parking.to_json()), 201

    @app.route('/client_parkings', methods=['DELETE'])
    def delete_client_parking():
        data = request.get_json()
        if not data or 'client_id' not in data or 'parking_id' not in data:
            return jsonify({'error': 'client_id and parking_id are required'}), 400

        client_parking = ClientParking.query.filter_by(
            client_id=data['client_id'],
            parking_id=data['parking_id'],
            time_out=None
        ).first()

        if not client_parking:
            return jsonify({'error': 'Client not parked at this parking'}), 404

        client = db.session.get(Client, data['client_id'])
        if not client or not client.credit_card:
            return jsonify({'error': 'Client has no credit card for payment'}), 400

        client_parking.time_out = datetime.now(timezone.utc)

        parking = db.session.get(Parking, data['parking_id'])
        if parking:
            parking.count_available_places += 1

        db.session.commit()
        db.session.refresh(client_parking)

        return jsonify(client_parking.to_json()), 200