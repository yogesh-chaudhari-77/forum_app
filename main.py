from config.config import config
from flask import Flask, render_template, jsonify, request, session, redirect
import uuid, datetime


"""
Add the Firebase Admin SDK to your server
Add the Firebase Admin SDK to your server (2021). Available at: https://firebase.google.com/docs/admin/setup (Accessed: 9 March 2021).
"""
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("./config/forum-28f86-firebase-adminsdk-laj3n-b037a8bd9e.json")
forum_app = firebase_admin.initialize_app(cred)
db = firestore.client()


app = Flask(__name__)
app.secret_key = 's3828116_secret_key'

# Defining a contex so that global variables can be accessed in the templates
"""
Templates — Flask Documentation (1.1.x)
Templates — Flask Documentation (1.1.x) (2021). Available at: https://flask.palletsprojects.com/en/1.1.x/templating/ (Accessed: 9 March 2021).
"""
@app.context_processor
def get_global_config():
  return {"config": config}

@app.route("/")
def home():
    return render_template("home.html");

@app.route("/login", methods = ['GET'])
def login_get():
    return render_template("login.html")


@app.route("/login", methods = ['POST'])
def login_post():

    # sanitise the input
    id = request.form['id']
    password = request.form['password']

    #form the response obj
    res = dict()

    # call firebase and validate this details with stored data
    docs = db.collection('users').where("id", "==", id).where("password", "==", password).get()

    for doc in docs:
        if doc.exists :
            user = doc.to_dict()
            if user['id'] == id and user['password'] == password:
                res["status"] = "success"

                # Setting the session data for tracking the user activity
                session['id'] = user['id']
                session['username'] = user['username']
                #session['profile_picture'] = user['profile_picture']
            else :
                res["status"] = "failed"
        break

    # Not Doc did not found
    if len(docs) == 0 :
        res["status"] = "failed"

    return jsonify(res)

@app.route("/register", methods = ['GET'])
def register_get():
    return render_template("register.html")


@app.route("/register", methods = ['POST'])
def register_post():

    user_id = request.form['id']
    username = request.form['username']
    password = request.form['password']

    res = {}

    # Check if the id matches with any of the documents
    docs = db.collection('users').where("id", "==", user_id).get()
    print(len(docs))
    if len(docs) != 0 :
        return jsonify({'status' : 'failed', 'err_msg' : 'The ID already exists'})

    # Check if the username matches with any of documents
    docs = db.collection('users').where("username", "==", username).get()
    print(len(docs))
    if len(docs) != 0 :
        return jsonify({'status' : 'failed', 'err_msg' : 'The username already exists'})

    # If both are unique then form data packet for new user
    new_user = {
        'id': user_id,
        'username': username,
        'password': password,
        'timestamp': (str(datetime.datetime.now()).split("."))[0]
    }

    # Add to firestore collection posts - document id will be id provided by user
    db.collection('users').document(user_id).set(new_user)

    return jsonify({'status': "success"})


@app.route("/user/edit_password", methods=['POST'])
def edit_password() :

    res = dict()

    if validate_logged_in_status() == True :

        #Variable sanitizaztion
        user_id = session['id']
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        #Get the user document to match the password
        doc = db.collection("users").document(user_id).get();
        user_doc = doc.to_dict()

        #Password match
        if user_doc['password'] == old_password :

            #Update the password for this user
            db.collection("users").document(user_id).set({
                'password' : new_password
            }, merge=True)

            return jsonify({'status':'success'})
        else:
            #Old password did not match with the database entry
            return jsonify({'status':'failed', 'err_msg':"The old password is incorrect"})

    else :
        # User is not logged in
        return redirect('/login', code=304)



@app.route('/logout', methods=['GET'])
def logout():
    # Unsetting the session variables
    session.pop('username', None)
    session.pop('id', None)

    # Redirecting to login page
    return redirect("/login", code=304);


@app.route("/forum", methods=['GET'])
def forum_get():
    return render_template("forum.html")


@app.route("/forum", methods=['POST'])
def forum_post():

    # sanitise the input
    subject = request.form['post_subject']
    message = request.form['post_message']
    #image = request.form['post_image']
    post_id = str(uuid.uuid4())
    timestamp = (str(datetime.datetime.now()).split("."))[0]

    #Forming firestore document
    message = {
        'user_id' : session['id'],
        'post_id' : post_id,
        'subject' : subject,
        'message' : message,
        'image' : '',
        'timestamp' : timestamp
    }

    # Add to firestore collection posts
    db.collection('posts').document(post_id).set(message)

    return jsonify({ 'status' : "success", 'post' : message})


@app.route("/user_page", methods=['GET'])
def user_page_get():
    if validate_logged_in_status():
        return render_template('user_page.html')
    else :
        return redirect("/login", code=304);


@app.route("/posts/all", methods = ["GET"])
def all_posts_get():
    docs = db.collection('posts').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream()
    posts = [];
    for doc in docs :
        post = doc.to_dict()
        posts.append(post)

    return jsonify({'status':'success', 'posts':posts})


@app.route("/posts/user", methods = ["GET"])
def user_posts_get():
    docs = db.collection('posts').where('user_id', '==', session['id']).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream()
    posts = [];
    for doc in docs :
        post = doc.to_dict()
        posts.append(post)

    return jsonify({'status':'success', 'posts':posts})

@app.route("/posts/<id>", methods=['GET'])
def post_get(id):
    doc = db.collection('posts').document(id).get()

    if doc.exists:
        post = doc.to_dict();

    return jsonify({'status': 'success', 'post': post})


# Checks whether the session data is set or not. Used for authenticated routing
def validate_logged_in_status():

    if 'id' in session :
        return True
    else :
        return False

if __name__ == "__main__":
    app.run(debug=True)