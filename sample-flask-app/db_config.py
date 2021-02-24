from app import app
from flaskext.mysql import MySQL

mysql = MySQL()
 
# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'YOUR_DB_PASSWORD'
app.config['MYSQL_DATABASE_DB'] = 'cloud_user'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql.init_app(app)