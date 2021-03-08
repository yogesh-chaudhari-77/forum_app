import firebase_admin
from flask import Flask, render_template, jsonify, request
from config.config import config

from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("./config/forum-28f86-firebase-adminsdk-laj3n-b037a8bd9e.json")
forum_app = firebase_admin.initialize_app(cred)
db = firestore.client()
app = Flask(__name__)

# Defining a contex so that global variables can be accessed in the templates
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
    return "register_post"


@app.route("/forum", methods=['GET'])
def forum_get():
    return render_template("forum.html")


@app.route("/forum", methods=['POST'])
def forum_post():

    # sanitise the input
    subject = request.form['post_subject']
    message = request.form['post_message']
    #image = request.form['post_image']

    #Forming firestore document
    message = {
        'subject' : subject,
        'message' : message,
        'image' : ''
    }

    # Add to firestore collection posts
    db.collection('posts').add(message)

    return jsonify({ 'status' : "success"})

if __name__ == "__main__":
    app.run(debug=True)