#!/usr/bin/env python3

"""
Columbia W4111 Intro to databases
Vishal Dubey (vd2468)
Vineeth Vajipey (vv2373)

To run locally: python server.py

Go to http://localhost:8111 in your browser
A debugger such as "pdb" may be helpful for debugging.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, abort, session, flash, url_for
from datetime import timedelta
from db_setup import create_tables, engine

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

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
            
        context = fetch_dashboard_information(user_id, cuisine, boro, min_rating, max_rating)
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
    session.permanent = True
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

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    print("Logged out!")
    flash('You have been logged out.')
    return redirect('/')

dashboardData = {
  "user": {},
  "businesses": [],
  "pins": [],
  "groups": []
}

@app.route('/business/<int:business_id>')
def business_detail(business_id):      
    user_id = session.get('user_id')

    business_query = text("""
        SELECT b.business_id, b.business_name, b.street, b.zipcode, b.cuisine, b.latitude, b.longitude, b.boro,
               CASE WHEN p.business_id IS NOT NULL THEN TRUE ELSE FALSE END AS is_pinned
        FROM Business b
        LEFT JOIN Pin p ON b.business_id = p.business_id AND p.user_id = :user_id
        WHERE b.business_id = :business_id
    """)
    business = g.conn.execute(business_query, {
        "business_id": business_id,
        "user_id": user_id
    }).fetchone()
    
    if business is None:
      return "Business not found", 404
      
    inspection_query = text("""
        SELECT i.inspection_id, i.inspection_date, i.action, i.score, i.grade, i.inspection_type
        FROM Inspection i
        WHERE i.business_id = :business_id
    """)
    inspections = g.conn.execute(inspection_query, {"business_id": business_id}).fetchall()

    violation_query = text("""
        SELECT v.violation_id, v.code, v.description, v.violation
        FROM Violation v
        JOIN Inspection i ON v.inspection_id = i.inspection_id
        WHERE i.business_id = :business_id
    """)
    violations = g.conn.execute(violation_query, {"business_id": business_id}).fetchall()

    comment_query = text("""
        SELECT c.comment_id, c.title, c.message, c.rating, c.comment_date, u.first_name
        FROM Comment c
        JOIN User_Data u ON c.user_id = u.user_id
        WHERE c.business_id = :business_id
    """)
    comments = g.conn.execute(comment_query, {"business_id": business_id}).fetchall()
    
    print("inspections", inspections)
    print("violations", violations)
    print("comments", comments)
    print("business", business)
    
    return render_template('business_detail.html', business=business, inspections=inspections, violations=violations, comments=comments)

# Check if the user exists
def fetch_dashboard_information(user_id, cuisine=None, boro=None, min_rating=None, max_rating=None):
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
               b.latitude, b.longitude, b.boro, CAST(COALESCE(AVG(c.rating), 0) AS INTEGER) AS average_rating
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
    businesses = sorted(businesses, key=lambda b: b.average_rating, reverse=True)

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
    
    dashboardData['user'] = user_result
    dashboardData['businesses'] = businesses
    dashboardData['pins'] = pins
    dashboardData['groups'] = groups
    
    print("Fetched filtered data for user", user_id)
    return ret

@app.route('/business/<int:business_id>/comment', methods=['POST'])
def submit_comment(business_id):
  if not session.get('logged_in'):
      flash('You must be logged in to comment.')
      return redirect(url_for('business_detail', business_id=business_id))

  user_id = session.get('user_id')
  title = request.form.get('title')
  message = request.form.get('message')
  rating = request.form.get('rating')

  if not title or not message or not rating:
      flash('Title, message, and rating are required.')
      return redirect(url_for('business_detail', business_id=business_id))

  try:
      insert_comment_query = text("""
          INSERT INTO Comment (user_id, business_id, title, message, rating, comment_date)
          VALUES (:user_id, :business_id, :title, :message, :rating, CURRENT_DATE)
      """)
      g.conn.execute(insert_comment_query, {
          "user_id": user_id,
          "business_id": business_id,
          "title": title,
          "message": message,
          "rating": int(rating)
      })
      g.conn.commit()
      flash('Comment submitted successfully.')
  except Exception as e:
      print("Error inserting comment:", e)
      flash('An error occurred while submitting your comment.')

  return redirect(url_for('business_detail', business_id=business_id))

@app.route('/business/<int:business_id>/toggle_pin', methods=['POST'])
def toggle_pin(business_id):
  if not session.get('user_id'):
      print('User trying to pin but not logged in')
      flash('You must be logged in to pin a business.')
      return redirect(url_for('business_detail', business_id=business_id))

  user_id = session.get('user_id')

  try:
      pin_query = text("""
          SELECT * FROM Pin 
          WHERE business_id = :business_id AND user_id = :user_id
      """)
      pin = g.conn.execute(pin_query, {
          "business_id": business_id,
          "user_id": user_id
      }).fetchone()

      if pin:
          delete_pin_query = text("""
              DELETE FROM Pin 
              WHERE business_id = :business_id AND user_id = :user_id
          """)
          g.conn.execute(delete_pin_query, {
              "business_id": business_id,
              "user_id": user_id
          })
          print('Unpinned ', business_id, "!")
          flash('Business unpinned successfully.')
      else:
          insert_pin_query = text("""
              INSERT INTO Pin (user_id, business_id, color)
              VALUES (:user_id, :business_id, 'red')
          """)
          g.conn.execute(insert_pin_query, {
              "user_id": user_id,
              "business_id": business_id
          })
          print('Pinned ', business_id, "!")
          flash('Business pinned successfully.')

      g.conn.commit()
  except Exception as e:
      print("Error toggling pin:", e)
      flash('An error occurred while toggling the pin.')

  return redirect(url_for('business_detail', business_id=business_id))

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
