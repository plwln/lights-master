from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_user import UserManager
from flask_wtf.csrf import CSRFProtect
import sqlite3

app = Flask(__name__, static_url_path='/static')
app._set_static_folder = '/static'
app.config.from_object(Config)
db = SQLAlchemy(app)
# db.apply_driver_hacks(app,Config.SQLALCHEMY_DATABASE_URI, {'pool_size': 10})
migrate = Migrate(app, db)

from app import routes, models
user_manager = UserManager(app, db, models.User)
if not models.User.query.filter(models.User.username == 'member').first():
    user = models.User(
        username='member',
        password=user_manager.hash_password('Password1'),
    )
    db.session.add(user)
    db.session.commit()

# Create 'admin@example.com' user with 'Admin' and 'Agent' roles
if not models.User.query.filter(models.User.username == 'admin').first():
    user = models.User(
        username='admin',
        password=user_manager.hash_password('Password1'),
    )
    user.roles.append(models.Role(name='Admin'))
    user.roles.append(models.Role(name='Agent'))
    db.session.add(user)
    db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)

