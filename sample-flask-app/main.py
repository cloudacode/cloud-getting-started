# third-party imports
import pymysql
from flask import jsonify, flash, render_template, request, redirect
from werkzeug.security import generate_password_hash, check_password_hash

# local imports
from app import app
from models import Results
from db_config import mysql

# route
@app.route('/')
def index_page():
    return render_template('index.html')

@app.route('/user', methods=['GET'])
def users():
	conn = None
	cursor = None
	try:
		conn = mysql.connect()
		cursor = conn.cursor(pymysql.cursors.DictCursor)
		cursor.execute("SELECT * FROM cloud_user")
		rows = cursor.fetchall()
		res = jsonify(rows)
		res.state_code = 200
		return res
		# table = Results(rows)
		# table.border = True
		# return render_template('users.html', table=table)
	except Exception as e:
		print(e)
	finally:
		cursor.close()
		conn.close()

@app.route('/add', methods=['POST'])
def add_user():
	conn = None
	cursor = None
	try:
		if request.is_json:
			req = request.get_json()

			_name = req['name']
			_email = req['email']
			_password = req['password']
			_bio = req['bio']
		
		if _name and _email and _password and request.method == 'POST':
			#do not save password as a plain text
			_hashed_password = generate_password_hash(_password)
			sql = "INSERT INTO cloud_user(user_name, user_email, user_password, user_bio) VALUES(%s, %s, %s, %s)"
			data = (_name, _email, _hashed_password, _bio,)
			conn = mysql.connect()
			cursor = conn.cursor()
			cursor.execute(sql, data)
			conn.commit()
			return redirect('/user')
		else:
			return 'Error while adding user'
	except Exception as e:
		print(e)
	finally:
		cursor.close() 
		conn.close()

@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_user(id):
	conn = None
	cursor = None
	try:
		conn = mysql.connect()
		cursor = conn.cursor()
		cursor.execute("DELETE FROM cloud_user WHERE user_id=%s", (id,))
		conn.commit()
		return redirect('/user')
	except Exception as e:
		print(e)
	finally:
		cursor.close() 
		conn.close()

@app.errorhandler(404)
def not_found(error=None):
	message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
	res = jsonify(message)
	res.state_code = 404
    
	return res
	
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
