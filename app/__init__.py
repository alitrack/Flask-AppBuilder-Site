import logging
from flask import Flask
from flask_appbuilder import AppBuilder, SQLA
from flask_sqlalchemy import BaseQuery
from sqlalchemy.engine import Engine
from sqlalchemy import event
from .indexview import FABView

from flask_softdeletes.query import SoftDeletedQuery

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
logging.getLogger().setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object('config')
# db = SQLA(app)
db = SQLA(app,query_class=type('Query', (SoftDeletedQuery, BaseQuery),{}))
# appbuilder = AppBuilder(app, db.session, base_template='mybase.html', indexview=FABView)
appbuilder = AppBuilder(app, db.session, indexview=FABView)


"""
Only include this for SQLLite constraints
"""
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
    

from app import views, data
from app import api
@app.before_first_request
def initDB():
    db.create_all()
    # data.fill_gender()
    # data.fill_data()


