from os import getenv
from secrets import token_hex

from dotenv import load_dotenv
from flask import Flask

from models import db, Department

load_dotenv()

DB_NAME = getenv('DB_NAME')
DB_USER = getenv('DB_USER')
DB_PW = getenv('DB_PASSWORD')
DB_HOST = getenv('DB_HOST')
DB_PORT = getenv('DB_PORT')

app = Flask(__name__)
app.config['SECRET_KEY'] = token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PW}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/departments', methods=['GET'])
def get_departments():
    departments = Department.query.all()
    return [dep.name for dep in departments]

if __name__ == "__main__":
    app.run(host='localhost', port=4000)