#!/usr/bin/env python3

"""
Columbia W4111 Intro to databases

To run locally: python server.py

Go to http://localhost:8111 in your browser
A debugger such as "pdb" may be helpful for debugging.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, abort, session, flash
from db_setup import create_tables, engine

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

app.secret_key = os.urandom(24)

create_tables()

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around home() that means:
#   run home() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def home():
  print(request.args)
  if session.get('logged_in') and session.get('user_id'):
    user_id = session['user_id']
    try:
        context = fetch_user_data(user_id)
        return render_template("dashboard.html", **context)
    except ValueError as e:
        print("Error fetching home data, ", e)
        flash(str(e))
        session.clear()
        return redirect('/')
  else:
      return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
  cursor = g.conn.execute(text("SELECT * FROM User_Data WHERE email = :email1 LIMIT 1;"), {
    "email1": request.form['email']
  })
  result = cursor.fetchone()
  if result:
    user_id = result._mapping['user_id']
    session['logged_in'] = True
    session['user_id'] = user_id
    return redirect('/')
  else:
    errMsg = 'No user found!'
    print(errMsg)
    flash(errMsg)
    return redirect('/')
  
@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    phone_number = request.form['phone_number']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    age = request.form['age']
    # password = request.form['password']

    try:
        g.conn.execute(text("""
            INSERT INTO User_Data (email, phone_number, first_name, last_name, age)
            VALUES (:email, :phone_number, :first_name, :last_name, :age)
        """), {
            "email": email,
            "phone_number": phone_number,
            "first_name": first_name,
            "last_name": last_name,
            "age": age
        })
        g.conn.commit()
        flash('Sign up successful! Please log in.')
        return redirect('/')
    except Exception as e:
        print("Error during sign up:", e)
        flash('Sign up failed. Please try again.')
        return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    print("Logged out!")
    flash('You have been logged out.')
    return redirect('/')

def fetch_user_data(user_id):
    # Check if the user exists
    user_query = text("SELECT * FROM User_Data WHERE user_id = :user_id")
    user_result = g.conn.execute(user_query, {"user_id": user_id}).fetchone()

    if not user_result:
        raise ValueError("Invalid user ID")

    # Fetch businesses with average ratings
    business_query = text("""
        SELECT b.business_id, b.business_name, b.street, b.zipcode, b.cuisine, b.latitude, b.longitude, b.boro, COALESCE(AVG(c.rating), 0) AS average_rating
        FROM Business b
        LEFT JOIN Comment c ON b.business_id = c.business_id
        GROUP BY b.business_id
    """)
    businesses = g.conn.execute(business_query).fetchall()

    # Fetch pins for the user
    pin_query = text("""
        SELECT p.pin_id, p.business_id, p.color
        FROM Pin p
        WHERE p.user_id = :user_id
    """)
    pins = g.conn.execute(pin_query, {"user_id": user_id}).fetchall()

    # Fetch groups the user has joined
    group_query = text("""
        SELECT g.group_id, g.group_title, g.group_description
        FROM Group_Data g
        JOIN Joins j ON g.group_id = j.group_id
        WHERE j.user_id = :user_id
    """)
    groups = g.conn.execute(group_query, {"user_id": user_id}).fetchall()

    ret = {
        "user": user_result,
        "businesses": businesses,
        "pins": pins,
        "groups": groups
    }
    print(ret)
    return ret


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
