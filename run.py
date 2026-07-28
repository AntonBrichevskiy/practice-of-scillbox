from app import create_app
from app.models import db, Client, Parking, ClientParking
from datetime import datetime

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Client': Client,
        'Parking': Parking,
        'ClientParking': ClientParking,
        'datetime': datetime
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)