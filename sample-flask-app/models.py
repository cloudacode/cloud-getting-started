from flask_table import Table, Col, LinkCol
 
class Results(Table):
    user_id = Col('Id')
    user_name = Col('Name')
    user_email = Col('Email')
    user_password = Col('Password')
    user_bio = Col('Bio')
    # user_password = Col('Password', show=False)