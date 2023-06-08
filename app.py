from flask import Flask, request, jsonify
import MySQLdb
from flask_cors import CORS
import hashlib, json
from dateutil.relativedelta import relativedelta
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

cors = CORS(app)

app.config['MYSQL_HOST'] = 'mysql'  # MySQL cluster host address
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

def sent_notification(userData,alarmFor,due_date):
    name = userData['firstname']
    userEmail = userData['emailId']
    subject = "IVMS - Sending Notification Alarm for "+ alarmFor
    body = "Dear "+name+",\n\nThis mail is to notify your " +alarmFor+" servicing due date was "+due_date.strftime('%Y-%m-%d')+ ". Please do the servicing as soon as possible."
    sender = "amburshabaz@gmail.com"
    sender_name = "IVMS"
    recipient = userEmail
    password = "achulbejvlouybtq"
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg["From"] = f"{sender_name} <{sender}>"
    msg['To'] = recipient
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, password)
       smtp_server.sendmail(sender, recipient, msg.as_string())
    print("Message sent!")

def checkServiceFindings(outData,flag):
    
    outFindings = {}    

    userData = outData['dataUserDetails']

    current_date = datetime.now().date()
    # Service
    last_svc_dt = outData['dataStreamingData']['Last_Service_Date']
    
    stdSvcPeriod = outData['dataStdThreshold']['ServicePeriodMonths']

    due_svc_date = last_svc_dt + relativedelta(months=stdSvcPeriod)

    outFindings['service_due_date'] = due_svc_date

    if due_svc_date < current_date:
        outFindings['service_alarm'] = True
        outFindings['service_no_of_days'] = (current_date - due_svc_date).days

        sent_notification(userData,'Vehicle Service',due_svc_date)
    else:
        outFindings['service_alarm'] = False
        outFindings['service_no_of_days'] = (current_date - due_svc_date).days

    #EngineOil
    last_eng_dt = outData['dataStreamingData']['Engine_Oil_Date']
    
    stdEngPeriod = outData['dataStdThreshold']['EngineOilPeriodMonths']

    due_eng_date = last_eng_dt + relativedelta(months=stdEngPeriod)

    outFindings['EngOil_due_date'] = due_eng_date

    if due_eng_date < current_date:
        outFindings['EngOil_alarm'] = True
        outFindings['EngOil_no_of_days'] = (current_date - due_eng_date).days
        
        sent_notification(userData,'Engine Oil',due_eng_date)
    else:
        outFindings['EngOil_alarm'] = False
        outFindings['EngOil_no_of_days'] = (current_date - due_eng_date).days
    
    #AirFilters
    last_airFlt_dt = outData['dataStreamingData']['Air_filters_SvcDate']
    
    stdAirFltPeriod = outData['dataStdThreshold']['AirFiltersMonths']

    due_airFlt_date = last_airFlt_dt + relativedelta(months=stdAirFltPeriod)

    outFindings['AirFlt_due_date'] = due_airFlt_date

    if due_airFlt_date < current_date:
        outFindings['AirFlt_alarm'] = True
        outFindings['AirFlt_no_of_days'] = (current_date - due_airFlt_date).days

        sent_notification(userData,'Air Filters',due_airFlt_date)
    else:
        outFindings['AirFlt_alarm'] = False
        outFindings['AirFlt_no_of_days'] = (current_date - due_airFlt_date).days

    #Gear Pressure
    latest_gear_pressure = int(outData['dataStreamingData']['GearPressure'])
    
    stdGearPressure = int(outData['dataStdThreshold']['GearPressure'])

    if latest_gear_pressure < stdGearPressure:
        outFindings['GearPr_alarm'] = True
        sent_notification(userData,'Gear Pressure',current_date)
    else:
        outFindings['GearPr_alarm'] = False

    #Battery
    latest_battery_percentage = int(outData['dataStreamingData']['VehicleBattery'])
    
    stdbattery_percentage = int(outData['dataStdThreshold']['VehicleBattery'])
    if latest_battery_percentage < stdbattery_percentage:
        outFindings['BatteryPercentage_alarm'] = True
        sent_notification(userData,'Vehcile Battery Percentage',current_date)
    else:
        outFindings['BatteryPercentage_alarm'] = False

    #Air Bags
    latest_gear_pressure = outData['dataStreamingData']['Air_bags']
    
    stdGearPressure = outData['dataStdThreshold']['AirBags']
    if latest_gear_pressure == stdGearPressure:
        outFindings['AirBags_alarm'] = False
        sent_notification(userData,'Air Bags',current_date)
    else:
        outFindings['AirBags_alarm'] = True
    return outFindings

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


@app.route('/myapp/user/data',methods=['GET','POST'])  # /myapp/user/data/1
def getUserData():
    params = request.json
    user_id = params['params']['user_id']
    #data = request.get_json()
    outData = {}
    conn = connect_mysql()
    cur = conn.cursor()
    cur.execute("select * from tblUserDetails where user_id = '"+user_id+"' ;")
    rows = cur.fetchall()
    dataUserDetails = []
    columns = [desc[0] for desc in cur.description]  # Get column names
    for row in rows:
        dataUserDetails.append(dict(zip(columns, row)))

    if len(rows) == 0:
        return {'result':'User doesn\'t exists'}
    
    for i in dataUserDetails:
        vehicleNumber = i['vechileNumber']

    cur.execute("select * from tblVehicleDetails where vehicleNumber = '"+vehicleNumber+"' ;")
    rows = cur.fetchall()
    dataVehicleDetails = []
    columns = [desc[0] for desc in cur.description]  
    for row in rows:
        dataVehicleDetails.append(dict(zip(columns, row)))
    
    cur.execute("select * from tblStdThreshold where vehicleNumber = '"+vehicleNumber+"' ;")
    rows = cur.fetchall()
    dataStdThreshold = []
    columns = [desc[0] for desc in cur.description]  
    for row in rows:
        dataStdThreshold.append(dict(zip(columns, row)))

    cur.execute("select * from tblStreamingData where vehicleNumber = '"+vehicleNumber+"'and received_dateTime = (select max(received_dateTime) from tblStreamingData where vehicleNumber = '"+vehicleNumber+"') ;")
    rows = cur.fetchall()
    dataStreamingData = []
    columns = [desc[0] for desc in cur.description] 
    for row in rows:
        dataStreamingData.append(dict(zip(columns, row)))
    
    cur.close()
    conn.close()

    outData['dataUserDetails'] = dataUserDetails[0]
    outData['dataVehicleDetails'] = dataVehicleDetails[0]
    outData['dataStreamingData'] = dataStreamingData[0]
    outData['dataStdThreshold'] = dataStdThreshold[0]

    # check services findings

    outData['outFindings'] = checkServiceFindings(outData,True)
    
    return outData

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=9090)
