from app import app
from flaskext.mysql import MySQL
import os

mysql = MySQL()
 
# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = os.environ['DB_USER']
app.config['MYSQL_DATABASE_PASSWORD'] = os.environ['DB_PASSWORD']
app.config['MYSQL_DATABASE_DB'] = os.environ['DB_NAME'] 
app.config['MYSQL_DATABASE_HOST'] = os.environ['DB_HOST'] 

mysql.init_app(app)