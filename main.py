#[11] - Introduction to flask
import os

from werkzeug.utils import secure_filename

from config.config import config
from flask import Flask, render_template, jsonify, request, session, redirect
import uuid, datetime

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud import storage

# Task 2
from google.cloud import bigquery

"""
Add the Firebase Admin SDK to your server
Add the Firebase Admin SDK to your server (2021). Available at: https://firebase.google.com/docs/admin/setup (Accessed: 9 March 2021).
"""
cred = credentials.Certificate("./config/forum-firebase-project-firebase-adminsdk-6imbv-9e7b32d5b3.json")
forum_app = firebase_admin.initialize_app(cred)
db = firestore.client()

"""
Authenticating as a service account  |  Authentication  |  Google Cloud
Authenticating as a service account  |  Authentication  |  Google Cloud (2021). Available at: https://cloud.google.com/docs/authentication/production (Accessed: 7 April 2021).
"""
storage_client = storage.Client.from_service_account_json('config/forum-google-cloud-service-account.json')

"""
Authenticating with a service account key file  |  BigQuery
Authenticating with a service account key file  |  BigQuery (2021). Available at: https://cloud.google.com/bigquery/docs/authentication/service-account-file (Accessed: 7 April 2021).
"""
bigquery_client = bigquery.Client.from_service_account_json('config/forum-google-cloud-service-account.json')


app = Flask(__name__)
app.secret_key = config['application']['secret_key']
app.config['UPLOAD_FOLDER'] = config['application']['upload_folder']

# Defining a contex so that global variables can be accessed in the templates
"""
[12] Templates — Flask Documentation (1.1.x)
Templates — Flask Documentation (1.1.x) (2021). Available at: https://flask.palletsprojects.com/en/1.1.x/templating/ (Accessed: 9 March 2021).
"""
@app.context_processor
def get_global_config():
  return {"config": config}

@app.route("/")
def home():
    return render_template("home.html");

# def allowed_file(filename):
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in config['application']['allowed_extensions']

def check_file_eligibility(filename):
    filename_tokens = os.path.splitext(filename)
    file_extension = filename_tokens[1]
    return (file_extension in config['application']['allowed_extensions'])


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

"""
[4] - Uploading File
Uploading Files — Flask Documentation (1.1.x)
Uploading Files — Flask Documentation (1.1.x) (2021). Available at: https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/ (Accessed: 9 March 2021).
Function that checks that file being uploaded is one of allowed types

[5] - Uploading Objects to Google Cloud
Uploading objects  |  Cloud Storage  |  Google Cloud
Uploading objects  |  Cloud Storage  |  Google Cloud (2021). Available at: https://cloud.google.com/storage/docs/uploading-objects#storage-upload-object-python (Accessed: 9 March 2021).

[6] - Read Firestore Data
Get data with Cloud Firestore  |  Firebase
Get data with Cloud Firestore  |  Firebase (2021). Available at: https://firebase.google.com/docs/firestore/query-data/get-data (Accessed: 9 March 2021).

[7] - Manage Firestore Data
Add data to Cloud Firestore  |  Firebase
Add data to Cloud Firestore  |  Firebase (2021). Available at: https://firebase.google.com/docs/firestore/manage-data/add-data (Accessed: 9 March 2021).
"""

@app.route("/register", methods = ['POST'])
def register_post():

    user_id = request.form['id']
    username = request.form['username']
    password = request.form['password']

    res = {}

    # Checking the status of file
    if 'file' in request.files:
        file = request.files['file']

        # [4] Saving file to server
        if file and file.filename != '' and check_file_eligibility(file.filename):

            filename = secure_filename(file.filename)
            file.save(os.path.join('/tmp/', filename));

            # [5] Upload the saved file to google cloud storage
            bucket = storage_client.bucket(config['google_cloud']['bucket_name'])
            source_file_name = filename  # Uploading recently saved file
            destination_blob_name = "profile_pictures/" + filename + "-" + str(uuid.uuid4())              # destination file name

            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(os.path.join('/tmp/', source_file_name));
            blob.make_public()

            # Delete the local file
            os.remove(os.path.join('/tmp/', filename));

    # [6] Check if the id matches with any of the documents
    docs = db.collection('users').where("id", "==", user_id).get()

    if len(docs) != 0 :
        return jsonify({'status' : 'failed', 'err_msg' : 'The ID already exists'})

    # [6] Check if the username matches with any of documents
    docs = db.collection('users').where("username", "==", username).get()

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

    # [7] Add to firestore collection posts - document id will be id provided by user
    db.collection('users').document(user_id).set(new_user)

    return jsonify({'status': "success"})


@app.route("/user/edit_password", methods=['POST'])
def edit_password() :

    res = dict()

    if validate_logged_in_status() == True :

        # Variable sanitizaztion
        user_id = session['id']
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        #Get the user document to match the password
        doc = db.collection("users").document(user_id).get();
        user_doc = doc.to_dict()

        # Password match
        if user_doc['password'] == old_password :

            # Update the password for this user
            db.collection("users").document(user_id).set({
                'password' : new_password
            }, merge=True)

            return jsonify({'status':'success'})
        else:
            # Old password did not match with the database entry
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
    if validate_logged_in_status():
        return render_template("forum.html")
    else :
        return redirect("/login", code=304);


"""
[4] - Uploading File
[5] - Uploading Objects to Google Cloud
"""
@app.route("/forum", methods=['POST'])
def forum_post():

    # sanitise the input
    post_id = str(uuid.uuid4())
    subject = request.form['post_subject']
    message = request.form['post_message']

    image_public_url = "";

    # Checking the status of file
    if 'file' in request.files:
        file = request.files['file']

        # Saving file to server
        if file and file.filename != '' and check_file_eligibility(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join('/tmp/', filename));
            # Upload the saved file to google cloud storage
            bucket = storage_client.bucket(config['google_cloud']['bucket_name'])
            source_file_name = filename                                 # Uploading recently saved file
            destination_blob_name = filename + "-" + str(uuid.uuid4())  # destination file name

            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(os.path.join('/tmp/', source_file_name));
            blob.make_public()
            image_public_url = blob.public_url

            # Delete the local file
            os.remove(os.path.join('/tmp/', filename))

    timestamp = (str(datetime.datetime.now()).split("."))[0]

    #Forming firestore document
    message = {
        'user_id' : session['id'],
        'post_id' : post_id,
        'subject' : subject,
        'message' : message,
        'image'   : image_public_url,
        'timestamp' : timestamp,
        'username' : session['username'],
        'user_image' : session['profile_picture']
    }

    # Add to firestore collection posts
    db.collection('posts').document(post_id).set(message)

    return jsonify({ 'status' : "success", 'post' : message})


"""
[4] - Uploading File
[5] - Uploading Objects to Google Cloud
"""
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
        if file.filename != '' and file and check_file_eligibility(file.filename):
            img_change = True
            filename = secure_filename(file.filename)
            file.save(os.path.join('/tmp/', filename));

            # Upload the saved file to google cloud storage
            bucket = storage_client.bucket(config['google_cloud']['bucket_name'])
            source_file_name = filename                                 # Uploading recently saved file
            destination_blob_name = filename + "-" + str(uuid.uuid4())  # destination file name

            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(os.path.join('/tmp/', source_file_name));
            blob.make_public()

            # Delete the local file
            os.remove(os.path.join('/tmp/', filename))

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


"""
[9], [10]
"""
@app.route("/posts/all", methods = ["GET"])
def all_posts_get():
    docs = db.collection('posts').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream()

    posts = [];
    for doc in docs :
        post = doc.to_dict()

        # Get posted by user's image
        user_doc = db.collection('users').document(post['user_id']).get()
        if user_doc.exists:
            user_doc_data = user_doc.to_dict();
            post['user_image'] = user_doc_data['profile_picture']
            post['username'] = user_doc_data['username']

        posts.append(post)

    return jsonify({'status':'success', 'posts':posts})


@app.route("/posts/user", methods = ["GET"])
def user_posts_get():
    docs = db.collection('posts').where('user_id', '==', session['id']).order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
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


@app.route("/attributions", methods=['GET'])
def attributions_get():
    return render_template('attributions.html')


@app.route("/query1", methods=['GET'])
def query_1():
    query = ('select * '
             'from '
             '(select '
             '      time_ref, sum(value) as trade_value '
             '      from `aerobic-star-307900.country_classification.gsquarterlySeptember20` '
             '      group by time_ref'
             ') '
             'order by trade_value desc '
             'limit 10'
             '')
    query_job = bigquery_client.query(query)
    rows = query_job.result()

    result = []
    i = 1
    for row in rows:
        print(row.time_ref, row.trade_value)
        result.append({'sr' : i, 'time_ref' : row.time_ref, 'trade_value' : row.trade_value })
        i = i + 1

    return render_template('task-2/query1.html', result=result)

@app.route("/query2", methods=['GET'])
def query_2():
    query = (''
             'Select '
             'A.country_code, B.country_code,'
             '(select country_label from `aerobic-star-307900.country_classification.country_classification` where country_code = A.country_code) as country_label ,'
             ' A.product_type, A.country_imports_value, B.country_emports_value, (A.country_imports_value - B.country_emports_value) as deficit_value, A.status '
             'from '
             '(SELECT country_code, product_type, status, sum(value) as country_imports_value from `aerobic-star-307900.country_classification.gsquarterlySeptember20` where account = \'Imports\' and product_type = \'Goods\' and time_ref between 201401 and 201612 and status = \'F\' group by country_code, product_type, status ) A '
             ' INNER JOIN '
             ' (SELECT country_code, sum(value) as country_emports_value from `aerobic-star-307900.country_classification.gsquarterlySeptember20` where account = \'Exports\' and product_type = \'Goods\' and time_ref between 201401 and 201612 and status = \'F\' group by country_code) B '
             ' ON '
             'A.country_code = B.country_code '
             'order by deficit_value desc '
              'limit 50 '
            )
    query_job = bigquery_client.query(query)
    rows = query_job.result()

    result = []
    i = 1
    for row in rows:
        result.append({'sr' : i, 'country_label' : row.country_label, 'product_type' : row.product_type, 'deficit_value' : row.deficit_value, 'status' : row.status})
        i = i + 1

    return render_template('task-2/query2.html', result=result)


@app.route("/query3", methods=['GET'])
def query_3():
    query = (''
             'select '
             '(select service_label from `aerobic-star-307900.country_classification.services_classification` where code = A.code) as service_label, '
             'B.service_export_value as service_export_value, '
             'A.service_import_value as service_import_value, '
             '(B.service_export_value - A.service_import_value) as surplus_value '
             'from '
             '(SELECT code, sum(value) as service_import_value from `aerobic-star-307900.country_classification.query_3_reduced_table` where account = \'Imports\' and product_type = \'Services\'  group by code ) A '
            'INNER JOIN'
            '(SELECT code, sum(value) as service_export_value from `aerobic-star-307900.country_classification.query_3_reduced_table` where account = \'Exports\' and product_type = \'Services\'  group by code ) B '
            'on A.code = B.code '
            'order by surplus_value desc '
            'limit 30 '
             )

    query_job = bigquery_client.query(query)
    rows = query_job.result()

    result = []
    i = 1
    for row in rows:
        result.append({'sr' : i, 'service_label' : row.service_label, 'surplus_value' : row.surplus_value })
        i = i + 1

    return render_template('task-2/query3.html', result=result)

# Checks whether the session data is set or not. Used for authenticated routing
def validate_logged_in_status():

    if 'id' in session :
        return True
    else :
        return False

if __name__ == "__main__":
    app.run(debug=True)

