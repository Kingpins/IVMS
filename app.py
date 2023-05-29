from flask import Flask, request, jsonify
import MySQLdb
from flask_cors import CORS
import hashlib, json

app = Flask(__name__)

cors = CORS(app)

app.config['MYSQL_HOST'] = 'localhost'  # MySQL cluster host address
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'vehicle_maintenance'  # MySQL username
app.config['MYSQL_PASSWORD'] = 'vehicle_maintenance_123'  # MySQL password
app.config['MYSQL_DB'] = 'VehicleMaintenance' 

def connect_mysql():
    conn = MySQLdb.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB'],
        port=app.config['MYSQL_PORT']
    )
    return conn

@app.route('/myapp/user/register',methods=['POST','GET'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        data['password'] = hashlib.md5(data['password'].encode('utf8')).hexdigest()
        conn = connect_mysql()
        cur = conn.cursor()

        checkUserQuery = "SELECT COUNT(*) FROM tblLogin WHERE username = %(username)s"
        cur.execute(checkUserQuery, data)
        result = cur.fetchone()

        if result[0] > 0:
            cur.close()
            conn.close()
            return {'result': 'failed, user already exists' } #"Username already exists. Please choose a different username."
        else:
            loginQuery = """
                    INSERT INTO tblLogin (
                        username, password
                    ) VALUES (
                        %(username)s, %(password)s
                    )
                """
            userDetailQuery = """
                    INSERT INTO tblUserDetails (
                        city, dealer, dob, driverLicense, emailId, firstname, fuelType,
                        gender, lastname, location, mobileno, pincode, registrationNumber,
                        state, street, vechileNumber, vehicleType, yop
                    ) VALUES (
                        %(city)s, %(dealer)s, %(dob)s, %(driverLicense)s, %(emailId)s, %(firstname)s,
                        %(fuelType)s, 'Male', %(lastname)s, %(location)s, %(mobileno)s,
                        %(pincode)s, %(registrationNumber)s, %(state)s, %(street)s,
                        %(vechileNumber)s, %(vehicleType)s, %(yop)s
                    )
                """
            cur.execute(loginQuery, data)
            cur.execute(userDetailQuery, data)
            conn.commit()
            cur.close()
            conn.close()
            return {'result': 'success' }


@app.route('/myapp/user/login',methods=['POST'])
def login():
    data = request.get_json()
    conn = connect_mysql()
    cur = conn.cursor()
    data['password'] = hashlib.md5(data['password'].encode('utf8')).hexdigest()
    cur.execute("select * from tblLogin where username = '"+data['username']+"' and password = '"+data['password']+"';")
    rows = cur.fetchall()
    data = []
    columns = [desc[0] for desc in cur.description]  # Get column names
    for row in rows:
        data.append(dict(zip(columns, row)))
    cur.close()
    conn.close()
    for i in data:
        user_id = i['user_id']
    if len(rows) == 0:
        response = {'result': 'failed' }
    else:
        response = {'result': 'success','user_id':user_id} # sent user_id
    
    return jsonify(response)


@app.route('/myapp/user/data',methods=['POST'])
def getUserData():
    data = request.get_json()
    conn = connect_mysql()
    cur = conn.cursor()
    cur.execute("select * from tblUserDetails where user_id = '"+data['user_id']+"' ;")
    rows = cur.fetchall()
    data = []
    columns = [desc[0] for desc in cur.description]  # Get column names
    for row in rows:
        data.append(dict(zip(columns, row)))
    cur.close()
    conn.close()
    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True,port=9090)
