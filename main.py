import os

from werkzeug.utils import secure_filename

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
from google.cloud import storage

cred = credentials.Certificate("./config/forum-firebase-project-firebase-adminsdk-6imbv-9e7b32d5b3.json")
forum_app = firebase_admin.initialize_app(cred)
db = firestore.client()

storage_client = storage.Client.from_service_account_json('config/forum-google-cloud-service-account.json')


app = Flask(__name__)
app.secret_key = config['application']['secret_key']
app.config['UPLOAD_FOLDER'] = config['application']['upload_folder']

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

"""
Uploading Files — Flask Documentation (1.1.x)
Uploading Files — Flask Documentation (1.1.x) (2021). Available at: https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/ (Accessed: 9 March 2021).
Function that checks that file being uploaded is one of allowed types
"""
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config['application']['allowed_extensions']

@app.route("/", methods=["POST"])
def home_post():

    if request.method == 'POST':
        if 'file' not in request.files:
            return ({"status": "failed", "err_msg":"No file found. Please try again"});
        file = request.files['file']

        if file.filename == '':
            return ({"status": "failed", "err_msg":"Please select a file and try again"});

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))      #Saving file to server

        # Upload the saved file to google cloud storage
        bucket = storage_client.bucket(config['google_cloud']['bucket_name'])
        source_file_name = os.path.join(app.config['UPLOAD_FOLDER'], filename)  #Uploading recently saved file                                           #
        destination_blob_name = filename+"-"+str(uuid.uuid4())                  #destination file name

        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name);

        #Delete the local file
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        return ({"status": "success"});
    else :
        return ({"status": "failed", "err_msg":"This must be a post request"});


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
                session['profile_picture'] = user['profile_picture']
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

    # Checking the status of file
    if 'file' in request.files:
        file = request.files['file']

        # Saving file to server
        if file.filename != '' and file and allowed_file(file.filename):
            img_change = True
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Upload the saved file to google cloud storage
            bucket = storage_client.bucket(config['google_cloud']['bucket_name'])
            source_file_name = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # Uploading recently saved file
            destination_blob_name = filename + "-" + str(uuid.uuid4())  # destination file name

            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(source_file_name);
            blob.make_public()

            # Delete the local file
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))

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
        'profile_picture': blob.public_url,
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
    session.pop('profile_picture', None)

    # and everything else
    session.clear()

    # Redirecting to login page
    return redirect("/login");


@app.route("/forum", methods=['GET'])
def forum_get():
    return render_template("forum.html")


@app.route("/forum", methods=['POST'])
def forum_post():

    # sanitise the input
    post_id = str(uuid.uuid4())
    subject = request.form['post_subject']
    message = request.form['post_message']

    #Checking the status of file
    if 'file' not in request.files:
        return ({"status": "failed", "err_msg": "No file found. Please try again"});
    file = request.files['file']

    if file.filename == '':
        return ({"status": "failed", "err_msg": "Please select a file and try again"});

    # Saving file to server
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Upload the saved file to google cloud storage
        bucket = storage_client.bucket(config['google_cloud']['bucket_name'])
        source_file_name = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # Uploading recently saved file
        destination_blob_name = filename + "-" + str(uuid.uuid4())  # destination file name

        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name);
        blob.make_public()

        # Delete the local file
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    timestamp = (str(datetime.datetime.now()).split("."))[0]

    #Forming firestore document
    message = {
        'user_id' : session['id'],
        'post_id' : post_id,
        'subject' : subject,
        'message' : message,
        'image'   : blob.public_url,
        'timestamp' : timestamp
    }

    # Add to firestore collection posts
    db.collection('posts').document(post_id).set(message)

    return jsonify({ 'status' : "success", 'post' : message})


@app.route("/edit_post", methods=['PUT'])
def edit_post():

    # sanitise the input
    post_doc_id = request.form['post_doc_id']
    post_id = request.form['post_id']
    subject = request.form['post_subject']
    message = request.form['post_message']
    img_change = False

    #Checking the status of file
    if 'file' in request.files:
        file = request.files['file']

        # Saving file to server
        if file.filename != '' and file and allowed_file(file.filename):
            img_change = True
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Upload the saved file to google cloud storage
            bucket = storage_client.bucket(config['google_cloud']['bucket_name'])
            source_file_name = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # Uploading recently saved file
            destination_blob_name = filename + "-" + str(uuid.uuid4())  # destination file name

            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(source_file_name);
            blob.make_public()

            # Delete the local file
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    timestamp = (str(datetime.datetime.now()).split("."))[0]

    #Forming firestore document
    message = {
        'user_id' : session['id'],
        'post_id' : post_id,
        'subject' : subject,
        'message' : message,
        'timestamp' : timestamp
    }

    # Img has been changed, and new image has been uploaded, so change the document as well
    if img_change:
        message['image'] = blob.public_url

    # Add to firestore collection posts
    db.collection('posts').document(post_id).set(message, merge=True)

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


"""
Uploading objects  |  Cloud Storage  |  Google Cloud
Uploading objects  |  Cloud Storage  |  Google Cloud (2021). Available at: https://cloud.google.com/storage/docs/uploading-objects#storage-upload-object-python (Accessed: 9 March 2021).
"""
@app.route("/upload", methods=["GET"])
def upload_blob():

    """Uploads a file to the bucket."""
    bucket_name = "forum-307005.appspot.com"
    source_file_name = "local/path/to/file"
    destination_blob_name = "storage-object-name"

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name);

    return jsonify({"status":"success"})

# Checks whether the session data is set or not. Used for authenticated routing
def validate_logged_in_status():

    if 'id' in session :
        return True
    else :
        return False

if __name__ == "__main__":
    app.run(debug=True)