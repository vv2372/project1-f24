# Restaurant Inspection & Rating App

### COMS 4111: Databases

### Vishal Dubey (vd2468) and Vineeth Vajipey (vv2732)

To run:

        source venv/bin/activate
        pip3 install -r requirements.txt
        cd webserver

        python3 server.py
                OR
        python3 server.py --debug

After running, visit:

        http://localhost:8111


- Get all information for a specific user.
- Get all business information for a specified user.

- Get all inspections for a given business.

- Get all violations for a given business and inspection combination.

- Get all pins for a given user.
- Create a pin for a given user, business, and color. Save this change in the database.

- Get all comments for a business
- Create a comment from the logged in user for a specific business. 

- Get all users in a group. 
- Get all groups
- Add a user to a group. 