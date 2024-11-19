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
from flask import Flask, request, render_template, g, redirect, Response, abort, session, flash
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

@app.route('/logout')
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
    business_query = text("""
        SELECT b.business_id, b.business_name, b.street, b.zipcode, b.cuisine, b.latitude, b.longitude, b.boro
        FROM Business b
        WHERE b.business_id = :business_id
    """)
    business = g.conn.execute(business_query, {"business_id": business_id}).fetchone()
    
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
    
    print(ret['businesses'])
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
            
        comments_query = text("""
            SELECT c.*, u.first_name, u.last_name
            FROM Comment c
            JOIN User_Data u ON c.user_id = u.user_id
            WHERE c.business_id = :business_id
            ORDER BY c.comment_date DESC
        """)
        comments = g.conn.execute(comments_query, {"business_id": business_id}).fetchall()
        
        violations_query = text("""
            SELECT v.*, i.inspection_date, i.grade
            FROM Violation v
            JOIN Inspection i ON v.inspection_id = i.inspection_id
            WHERE i.business_id = :business_id
            ORDER BY i.inspection_date DESC
        """)
        violations = g.conn.execute(violations_query, {"business_id": business_id}).fetchall()
        
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

# # User endpoints
# @app.route('/api/users/<int:user_id>')
# def get_user(user_id):
#     """Get all information for a specific user"""
#     if not session.get('logged_in'):
#         return {'error': 'Not logged in'}, 401
        
#     try:
#         query = text("""
#             SELECT user_id, email, phone_number, first_name, last_name, age, is_admin 
#             FROM User_Data 
#             WHERE user_id = :user_id
#         """)
#         result = g.conn.execute(query, {"user_id": user_id}).fetchone()
        
#         if not result:
#             return {'error': 'User not found'}, 404
            
#         return dict(result._mapping)
        
#     except Exception as e:
#         print("Error fetching user:", e)
#         return {'error': 'Database error'}, 500

# @app.route('/api/users/<int:user_id>/businesses')
# def get_user_businesses(user_id):
#     """Get all businesses a user has interacted with (commented on or pinned)"""
#     if not session.get('logged_in'):
#         return {'error': 'Not logged in'}, 401
        
#     try:
#         query = text("""
#             SELECT DISTINCT b.* 
#             FROM Business b
#             LEFT JOIN Pin p ON b.business_id = p.business_id
#             LEFT JOIN Comment c ON b.business_id = c.business_id
#             WHERE p.user_id = :user_id OR c.user_id = :user_id
#         """)
#         results = g.conn.execute(query, {"user_id": user_id}).fetchall()
#         return {'businesses': [dict(row._mapping) for row in results]}
        
#     except Exception as e:
#         print("Error fetching user businesses:", e)
#         return {'error': 'Database error'}, 500

# # Business endpoints
# @app.route('/api/businesses/<int:business_id>/inspections')
# def get_business_inspections(business_id):
#     """Get all inspections for a given business"""
#     try:
#         query = text("""
#             SELECT * FROM Inspection
#             WHERE business_id = :business_id
#             ORDER BY inspection_date DESC
#         """)
#         results = g.conn.execute(query, {"business_id": business_id}).fetchall()
#         return {'inspections': [dict(row._mapping) for row in results]}
        
#     except Exception as e:
#         print("Error fetching inspections:", e)
#         return {'error': 'Database error'}, 500

# @app.route('/api/inspections/<int:inspection_id>/violations')
# def get_inspection_violations(inspection_id):
#     """Get all violations for a given inspection"""
#     try:
#         query = text("""
#             SELECT * FROM Violation
#             WHERE inspection_id = :inspection_id
#         """)
#         results = g.conn.execute(query, {"inspection_id": inspection_id}).fetchall()
#         return {'violations': [dict(row._mapping) for row in results]}
        
#     except Exception as e:
#         print("Error fetching violations:", e)
#         return {'error': 'Database error'}, 500

# # Pin endpoints
# @app.route('/api/users/<int:user_id>/pins')
# def get_user_pins(user_id):
#     """Get all pins for a given user"""
#     if not session.get('logged_in'):
#         return {'error': 'Not logged in'}, 401
        
#     try:
#         query = text("""
#             SELECT p.*, b.business_name 
#             FROM Pin p
#             JOIN Business b ON p.business_id = b.business_id
#             WHERE p.user_id = :user_id
#         """)
#         results = g.conn.execute(query, {"user_id": user_id}).fetchall()
#         return {'pins': [dict(row._mapping) for row in results]}
        
#     except Exception as e:
#         print("Error fetching pins:", e)
#         return {'error': 'Database error'}, 500

# @app.route('/api/pins', methods=['POST'])
# def create_pin():
#     """Create a new pin"""
#     if not session.get('logged_in'):
#         return {'error': 'Not logged in'}, 401
        
#     try:
#         data = request.get_json()
#         query = text("""
#             INSERT INTO Pin (business_id, user_id, color)
#             VALUES (:business_id, :user_id, :color)
#             RETURNING pin_id
#         """)
#         result = g.conn.execute(query, {
#             "business_id": data['business_id'],
#             "user_id": session['user_id'],
#             "color": data['color']
#         })
#         g.conn.commit()
        
#         return {'pin_id': result.fetchone()[0]}, 201
        
#     except Exception as e:
#         print("Error creating pin:", e)
#         return {'error': 'Database error'}, 500

# # Comment endpoints
# @app.route('/api/businesses/<int:business_id>/comments')
# def get_business_comments(business_id):
#     """Get all comments for a business"""
#     try:
#         query = text("""
#             SELECT c.*, u.first_name, u.last_name
#             FROM Comment c
#             JOIN User_Data u ON c.user_id = u.user_id
#             WHERE c.business_id = :business_id
#             ORDER BY c.comment_date DESC
#         """)
#         results = g.conn.execute(query, {"business_id": business_id}).fetchall()
#         return {'comments': [dict(row._mapping) for row in results]}
        
#     except Exception as e:
#         print("Error fetching comments:", e)
#         return {'error': 'Database error'}, 500

# @app.route('/api/comments', methods=['POST'])
# def create_comment():
#     """Create a new comment"""
#     if not session.get('logged_in'):
#         return {'error': 'Not logged in'}, 401
        
#     try:
#         data = request.get_json()
#         query = text("""
#             INSERT INTO Comment (user_id, business_id, title, message, rating, comment_date)
#             VALUES (:user_id, :business_id, :title, :message, :rating, CURRENT_DATE)
#             RETURNING comment_id
#         """)
#         result = g.conn.execute(query, {
#             "user_id": session['user_id'],
#             "business_id": data['business_id'],
#             "title": data['title'],
#             "message": data['message'],
#             "rating": data['rating']
#         })
#         g.conn.commit()
        
#         return {'comment_id': result.fetchone()[0]}, 201
        
#     except Exception as e:
#         print("Error creating comment:", e)
#         return {'error': 'Database error'}, 500

# # Group endpoints
# @app.route('/api/groups/<int:group_id>/users')
# def get_group_users(group_id):
#     """Get all users in a group"""
#     try:
#         query = text("""
#             SELECT u.user_id, u.first_name, u.last_name, j.joined_at
#             FROM User_Data u
#             JOIN Joins j ON u.user_id = j.user_id
#             WHERE j.group_id = :group_id
#             ORDER BY j.joined_at DESC
#         """)
#         results = g.conn.execute(query, {"group_id": group_id}).fetchall()
#         return {'users': [dict(row._mapping) for row in results]}
        
#     except Exception as e:
#         print("Error fetching group users:", e)
#         return {'error': 'Database error'}, 500

# @app.route('/api/groups')
# def get_groups():
#     """Get all groups"""
#     try:
#         query = text("""
#             SELECT g.*, COUNT(j.user_id) as member_count
#             FROM Group_Data g
#             LEFT JOIN Joins j ON g.group_id = j.group_id
#             GROUP BY g.group_id
#         """)
#         results = g.conn.execute(query).fetchall()
#         return {'groups': [dict(row._mapping) for row in results]}
        
#     except Exception as e:
#         print("Error fetching groups:", e)
#         return {'error': 'Database error'}, 500

# @app.route('/api/groups/<int:group_id>/join', methods=['POST'])
# def join_group(group_id):
#     """Add a user to a group"""
#     if not session.get('logged_in'):
#         return {'error': 'Not logged in'}, 401
        
#     try:
#         query = text("""
#             INSERT INTO Joins (user_id, group_id, joined_at)
#             VALUES (:user_id, :group_id, CURRENT_DATE)
#         """)
#         g.conn.execute(query, {
#             "user_id": session['user_id'],
#             "group_id": group_id
#         })
#         g.conn.commit()
        
#         return {'message': 'Successfully joined group'}, 201
        
#     except Exception as e:
#         print("Error joining group:", e)
#         return {'error': 'Database error'}, 500

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
