# Project 1, Part 3

* Assigned: 10/10
* Due:  11/12 10AM EST
* (worth 50% of overall Project 1 grade)

In this part of the project, you will either (3a) complete the web application by building the front end
on top of the `Flask` Python webserver, or (3b) expand your schema design.


* [Project overview](http://github.com/w4111/project1)
* If your teammate has dropped the class, [see the contingency plan](https://github.com/w4111/project1-s19/blob/master/part1.md#contingency)
* For any questions about collaboration, [see the Syllabus](https://github.com/w4111/w4111.github.io/blob/master/syllabus.md#cheating)
* If there are questions of general interest, please post to the discussion board.


## Requirements for 3a: Web front-end

Implement the application you described in Part 1 in Python using Flask.

* Your application must execute SQL query strings on the provided staff database. (*Note*: This means you cannot use an ORM. Part of the goal of this project is to practice writing and debugging SQL queries. Tools that attempt to make this "easier" are not permitted.)
* Your application must provide a way to view or interact with all the entities and relationships in your final ER diagram.
* It does not need to be beautiful or sophisticated. Plain text pages are acceptable! However, if you want to make it fancy, you can do that (there will be a few "bonus" prizes for sophisticted applications).
* In general, you can probably use whatever third-party libraries you want, except for ORMs or other libraries that simplify database access. If you are unsure if a library is permitted, ask a staff member or on the discussion board.
* Your application should prevent forms of SQL injection described in lecture.

*Note*: if you anticipate doing a huge number of queries (say hundreds of queries per second), 
or will have a huge database (more than 10k rows),
please let the staff know so we can allocate resources appropriately.



### Getting Started

We have written [extensive instructions](./programming.md) to help you get set up.


Your job is to implement your proposed web application.  To help you out,
we have provided a bare-bones Flask web application in [./webserver/](./webserver/) which implemented in Python 2.7. **You can build upon this starter code using Python 2.7 or change to Python 3 by referring to the official [Flask tutorial](http://flask.pocoo.org/docs/latest/tutorial/) and [Python 3 tutorial](https://docs.python.org/3.7/tutorial/).**
It provides code that connects to a database url, and a default index page.
Take a look at the comments in `server.py` to see how to use modify the server.
You will need to connect to the class database (used for part 2).

Please read all these directions, and get the example server we provide running. Once you get it
running you should edit it to talk to your own database and start working on your custom logic.



### Grading

* How well your application matches the Part 1 submission, and how well you incorporated the mentor's feedback?
* Does it let a user access all the entities and relationships on the ER diagram?
* Your grade will not be based on how _sophisticated_ the user interface is (though it may mildly help)
* Your grade will suffer if it doesn't work, requires the user typing SQL, crashes or
  locks up on bad inputs, is vulnerable to the SQL injection described in lecture, and otherwise does
  not work as you described in part 1.

85% will be for the demo you do with your mentor. 
15% will be for what you submit to Gradescope. 
 
As per Lecture 1, no grace days are allowed for Project 1 Part 3. 
Late submissions are docked 25% per day.
 
Therefore, the penalty for being late on the Project 1 Part 3 PDF submission to Gradescope will be a 25% dock imposed on the PDF submission, so 25% on that 15%, per day it is late.

### Submission

Please leave your virtual machine running so the IP address does not change (see "Longer Term Running" above), then submit a PDF file to Gradescope containing:

* both members' name and UNI;
* the URL to access your application;
    * if your application has some authentication flow (i.e. some sign-in page), include such credentials as well;
* link to the GitHub repo containing your codebase;
    * if you make any changes to your repo after you submitted your PDF file, we'll consider it as submission date instead;
* any changes made to your schema since Part 2 (and why);



Students will present to their project mentor between `11/12` and `11/20`.

[Make an appointment with TAs](https://calendar.google.com/calendar/embed?src=v79hsp9qikue2f3s4bkdemsu4c%40group.calendar.google.com&ctz=America%2FNew_York)


Contact your mentor immediately if you cannot make it by `11/12`.

You will show off your project using the mentor's web browser:

1. Give your mentor the app's URL so they can run it in Chrome or Firefox -- make sure you tested in those browsers!
    * your grade will suffer _considerably_ if this step doesn't work

2. Your mentor will interact with your application and test the functionality described in Part 1
    *  Have a number of example interactions prepared ahead of time to show your mentor.  
       The more you impress your mentor, the better your grade is likely to be.

3. Your mentor may ask to look at your code, so have it available.  

4. The web interface doesn't need to be fancy, however users **should not need to type anything resembling SQL**.



## Requirements for 3b: Expanded schema design

If you are following the Expanded-Design Option:

1. Extend the ER diagram from Part 1 to support a new hypothetical set of features.   The expansion should increase the number of entity sets, relationship sets, and overall "complexity" of the design by roughly 50%. 
  * This expansion should be substantial: rather than just adding a few entity sets and relationship sets that are overly similar to Part 1, you are expected to add a truly novel and significant component to your database (following the above "50% increase in complexity" guidelines). 
  * For example, if your Part 1 database follows some variant of the Amazon shopping site, a substantial expansion for Part 3 could be the addition of a sophisticated "subsystem" for product reviews and ratings, as well as for allowing users to vote on the usefulness of the reviews from other customers, etc.

2. Extend your SQL schema from Part 2 of your database on our PostgreSQL server to include the mapping of all new entity sets and relationship sets, following the directions in Part 2 of the project on how to specify constraints in your expanded SQL design.
3. Add tuples to your new tables on our PostgreSQL server, following the guidelines on the number of tuples from Part 2 of the project.
4. Write a short paragraph (no more than 20 lines) that describes the application-level features that would build on top of your expansion.
5. Write 3 "interesting" SQL queries, with a sentence or two per query to explain what the query is supposed to do.   Each query should involve one or more of the new tables in your expansion.    The queries should run if the staff copy-and-pastes the query text into a SQL prompt..  


### Submission 

You will submit this part of the project electronically on Gradescope directly, along the lines of what you did for Part 2.
There are no grace days for this part of the project. Just as for Parts 1 and 2, you should submit your project exactly once per team, rather than once per student. (Click on "Add Group Member" after one of you has submitted your project.) You should submit one or more (uncompressed) files containing:

* The name and UNI of both teammates.
* The PostgreSQL account name for your database on our server (i.e., specify which teammate's UNI we should use to identify the database for your team.) This will normally be the same database that you used for Part 2, but we need you to confirm that we should check that database.
* Your paragraph that describes the application-level features enabled by your expansion.
* A textual description of your extensions on the database design, explaining which entity sets and relationship sets are new, and how you mapped them to SQL statements.
* Your new, complete ER diagram, including all of your entity sets and relationship sets, both from Part 1 and the new ones from Part 3.
* The `CREATE TABLE` statements and any other elements of the full database that you created on your PostgreSQL database. (We will of course also check the schema directly on the database server, but we need as well the statements as part of your submission file.) You should include all of your tables, not just the new ones for Part 3.
* Your 3 "interesting" SQL queries.


### Grading 


Your grade will be a function of how well you have incorporated any feedback that your project mentor has given you, and the following factors:

* Quality of your expanded ER diagram: We will evaluate how well your expanded ER diagram implements your plans for the Expanded-Design Option from Part 1, and how well your expanded ER diagram models your application, including how well you modeled any relevant real-world constraints.
* Quality of your expanded SQL schema and implementation on PostgreSQL: We will evaluate how well you mapped your expanded ER diagram, including constraints, into a SQL schema on PostgreSQL, using the techniques that we covered in class.
* Quality of your expanded constraint handling: We will evaluate how well you managed to capture real-world constraints of your expanded design through primary key, foreign key, unique, and good-style attribute- and tuple-based CHECK constraints.
* Quality of the expanded real-world (or at least realistic) data that you loaded into the expanded database on PostgreSQL.



