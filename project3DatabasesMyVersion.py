
import os
import sys
import oracledb
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect

db_user = "ADMIN"
db_password = "Martinisgoat1!"
db_connect = "(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1521)(host=adb.us-ashburn-1.oraclecloud.com))(connect_data=(service_name=g14f988a10ff21c_lmcin003database_tp.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))"

def init_session(connection, requestedTag_ignored):
    cursor = connection.cursor()
    cursor.execute("""
        ALTER SESSION SET
          TIME_ZONE = 'UTC'
          NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI'""")


# start_pool(): starts the connection pool
def start_pool():

    # Generally a fixed-size pool is recommended, i.e. pool_min=pool_max.
    # Here the pool contains 4 connections, which is fine for 4 conncurrent
    # users.
    #
    # The "get mode" is chosen so that if all connections are already in use, any
    # subsequent acquire() will wait for one to become available.

    pool_min = 1
    pool_max = 2
    pool_inc = 0
    pool_gmd = oracledb.SPOOL_ATTRVAL_WAIT

    print("Connecting to", db_connect)

    pool = oracledb.SessionPool(user=db_user,
                                 password=db_password,
                                 dsn=db_connect,
                                 min=pool_min,
                                 max=pool_max,
                                 increment=pool_inc,
                                 threaded=True,
                                 getmode=pool_gmd,
                                 sessionCallback=init_session)

    return pool



app = Flask(__name__)

def output_type_handler(cursor, metadata):

    def out_converter(d):
        print( d )
        if d is None:
            return ""
        else:
            return d

    if metadata.type_code is oracledb.DB_TYPE_NUMBER:
        return cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=cursor.arraysize, outconverter=out_converter, convert_nulls=True)





################################################################################ Project3 Student version below
# CUSTOMER Table
def doInsertCustomer(customer_id, name, email, billing_address, payment_info):
    connection = pool.acquire()
    cur = connection.cursor()
    try:
        cur.execute(
        "INSERT INTO CUSTOMER (CustomerID, Name, Email, BillingAddress, PaymentInformation) VALUES (:customer_id, :name, :email, :billing_address, :payment_info)",
        [customer_id, name, email, billing_address, payment_info])
    except oracledb.Error as error:
        print(error)
    
    #cur.close()
    connection.commit()
def doUpdateCustomer(customer_id, name, email, billing_address, payment_info):
    connection = pool.acquire()
    cur = connection.cursor()
    try:
        cur.execute(
        "UPDATE CUSTOMER SET Name = :name, Email = :email, BillingAddress = :billing_address, PaymentInformation = :payment_info WHERE CustomerID = :customer_id",
        [name, email, billing_address, payment_info, customer_id]
        )
    except oracledb.Error as error:
        print(error)

    #cur.close()
    connection.commit()

def doDeleteCustomer(customer_id):
    connection = pool.acquire()
    cur = connection.cursor()
    try:
        cur.execute("DELETE FROM CUSTOMER WHERE CustomerID = :customer_id", [customer_id])
    except oracledb.Error as error:
        print(error)
    #cur.close()
    connection.commit()
def doSelectCustomerAll():
    connection = pool.acquire()
    cur = connection.cursor()
    cur.outputtypehandler = output_type_handler
    cur.execute("SELECT * FROM CUSTOMER")
    columns = [col[0] for col in cur.description]
    cur.rowfactory = lambda *args: dict(zip(columns, args))

    data = cur.fetchall()

    connection.close()
    return (data)

    

def doSelectCustomerPK(customer_id):
    connection = pool.acquire()
    cur = connection.cursor()
    cur.outputtypehandler = output_type_handler

    cur.execute("SELECT * FROM CUSTOMER WHERE CustomerID = :customer_id", [customer_id])
    
    columns = [col[0] for col in cur.description]
    cur.rowfactory = lambda *args: dict(zip(columns, args))

    data = cur.fetchone()
    connection.close()
    if data:
        # Map database keys to expected template-friendly keys
        mapped_data = {
            'CustomerID': data.get('CUSTOMERID', ''),
            'name': data.get('NAME', ''),
            'email': data.get('EMAIL', ''),
            'billing_address': data.get('BILLINGADDRESS', ''),
            'payment_info': data.get('PAYMENTINFORMATION', '')
        }
        return mapped_data
    else:
        return None

#######################################################################

@app.route('/')
@app.route('/index')
def index():

    return customerAll()

@app.route('/customer/<int:customer_id>')
def show_customer(customer_id):
    customer_data = doSelectCustomerPK(customer_id)

    if customer_data:
        return render_template('CustomerDetailMyVersion.html', title='Customer Detail', data=customer_data)
    else:
        return "<h1>Customer not found</h1>", 404
    
@app.route('/post/customer/<int:customer_id>', methods=['POST']) 
def update_customer(customer_id):
    name = request.form.get('name')
    email = request.form.get('email')
    billing_address = request.form.get('billing_address')
    payment_info = request.form.get('payment_info')

    doUpdateCustomer(customer_id, name, email, billing_address, payment_info)
    return redirect(f"/customer/{customer_id}")

@app.route('/delete/customer/<int:customer_id>', methods=['post']) 
def delete_customer(customer_id):
    doDeleteCustomer(customer_id)
    return redirect("/customerall/")


@app.route('/customerall/')
def customerAll():
    row = doSelectCustomerAll()
    return render_template('CustomerList.html', title='Customer List', data = row)


@app.route('/create/')
def create():
    return render_template('CustomerCreate.html', title='CustomerCreate')


@app.route('/insert/customer/',  methods=['post'])
def customerCreate():
    customer_id = request.form.get('customer_id')
    name = request.form.get('name')
    email = request.form.get('email')
    billing_address = request.form.get('billing_address')
    payment_info = request.form.get('payment_info')
    
    print("Received data:", customer_id, name, email, billing_address, payment_info)

    
    doInsertCustomer(customer_id, name, email, billing_address, payment_info)

    
    return redirect('/customerall/')
	



##############################################################################
#
# Initialization is done once at startup time
#
if __name__ == '__main__':

    # Start a pool of connections
    pool = start_pool()

    # Start a webserver
    app.run(port=int(os.environ.get('PORT', '8080')))
