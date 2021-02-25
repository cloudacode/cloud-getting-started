from app import app
from flaskext.mysql import MySQL

mysql = MySQL()
 
# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'cloudme'
app.config['MYSQL_DATABASE_DB'] = 'cloud_user'
app.config['MYSQL_DATABASE_HOST'] = 'db'

mysql.init_app(app)