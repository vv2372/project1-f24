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


@app.route('/')
def home():
    """
    Once logged in, this function fetches the user's data and gets the filter parameters from the request.
    It then renders the dashboard.html template.

    """
    print(request.args)
    if session.get('logged_in') and session.get('user_id'):
        user_id = session['user_id']
        try:
            cuisine = request.args.get('cuisine')
            boro = request.args.get('boro')
            min_rating = request.args.get('min_rating')
            max_rating = request.args.get('max_rating')
            
            context = fetch_user_data(user_id, cuisine, boro, min_rating, max_rating)
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

def fetch_user_data(user_id, cuisine=None, boro=None, min_rating=None, max_rating=None):
    """
    This function fetches the user's data and the businesses that match the filter parameters.
    It then returns a dictionary containing the user's data, the businesses, and the pins and groups associated with the user.
    """
    user_query = text("SELECT * FROM User_Data WHERE user_id = :user_id")
    user_result = g.conn.execute(user_query, {"user_id": user_id}).fetchone()

    if not user_result:
        raise ValueError("Invalid user ID")

    query_parts = ["""
        SELECT b.business_id, b.business_name, b.street, b.zipcode, b.cuisine, 
               b.latitude, b.longitude, b.boro, COALESCE(AVG(c.rating), 0) AS average_rating
        FROM Business b
        LEFT JOIN Comment c ON b.business_id = c.business_id
    """]
    
    where_conditions = []
    params = {}
    
    if cuisine:
        where_conditions.append("b.cuisine = :cuisine")
        params["cuisine"] = cuisine
        
    if boro:
        where_conditions.append("b.boro = :boro")
        params["boro"] = boro
        
    if where_conditions:
        query_parts.append("WHERE " + " AND ".join(where_conditions))
        
    query_parts.append("GROUP BY b.business_id")
    
    having_conditions = []
    if min_rating:
        having_conditions.append("COALESCE(AVG(c.rating), 0) >= :min_rating")
        params["min_rating"] = float(min_rating)
    if max_rating:
        having_conditions.append("COALESCE(AVG(c.rating), 0) <= :max_rating")
        params["max_rating"] = float(max_rating)
        
    if having_conditions:
        query_parts.append("HAVING " + " AND ".join(having_conditions))

    business_query = text(" ".join(query_parts))
    businesses = g.conn.execute(business_query, params).fetchall()

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
        "groups": groups,

        "current_filters": {
            "cuisine": cuisine,
            "boro": boro,
            "min_rating": min_rating,
            "max_rating": max_rating
        }
    }
    print("Fetched filtered data for user", user_id)
    return ret

@app.route('/business/<int:business_id>')
def business_details(business_id):
    """
    Display detailed information about a specific business
    """
    if not session.get('logged_in'):
        return redirect('/')
        
    try:
        # Get business details
        business_query = text("""
            SELECT b.*, COALESCE(AVG(c.rating), 0) as average_rating, COUNT(c.comment_id) as review_count
            FROM Business b
            LEFT JOIN Comment c ON b.business_id = c.business_id
            WHERE b.business_id = :business_id
            GROUP BY b.business_id
        """)
        business = g.conn.execute(business_query, {"business_id": business_id}).fetchone()
        
        if not business:
            flash('Business not found!')
            return redirect('/')
            
        # Get comments
        comments_query = text("""
            SELECT c.*, u.first_name, u.last_name
            FROM Comment c
            JOIN User_Data u ON c.user_id = u.user_id
            WHERE c.business_id = :business_id
            ORDER BY c.comment_date DESC
        """)
        comments = g.conn.execute(comments_query, {"business_id": business_id}).fetchall()
        
        # Get violations
        violations_query = text("""
            SELECT v.*, i.inspection_date, i.grade
            FROM Violation v
            JOIN Inspection i ON v.inspection_id = i.inspection_id
            WHERE i.business_id = :business_id
            ORDER BY i.inspection_date DESC
        """)
        violations = g.conn.execute(violations_query, {"business_id": business_id}).fetchall()
        
        # Check if business is pinned by current user
        pin_query = text("""
            SELECT * FROM Pin 
            WHERE business_id = :business_id AND user_id = :user_id
        """)
        pin = g.conn.execute(pin_query, {
            "business_id": business_id,
            "user_id": session['user_id']
        }).fetchone()
        
        return render_template(
            'business_details.html',
            business=business,
            comments=comments,
            violations=violations,
            is_pinned=bool(pin)
        )
        
    except Exception as e:
        print("Error fetching business details:", e)
        flash('Error fetching business details')
        return redirect('/')

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
