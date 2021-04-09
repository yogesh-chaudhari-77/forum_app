# Cloud Based Forum Application

Created simple forum application to demonstrate the understanding of -
* Google Cloud Platform
* Google App Engine
* Firebase Firestore database
* Google Cloud Storage
* Big Query

# Key Learnings

* Creating and Managing google cloud service accounts, Billing, Budgets and Notifications
* Deploying application to Google App Engine Platform
* Troubleshooting
* Basic CRUD operations with Firebase Database and data modeling
* Effects of firebase data structuring on Pricing and Data transfer speed
* Uploading Objects to Google Cloud Storage
* Managing Bucket Policies, Making objects publically available.

# Application features

User can create an account using a unique user id and username.
Once registered, user has access to all the posts made by other users. User can post a message with fields such subject, message and upload an optional picture.
Once posted, message fields are stored in the firestore and picture is uploaded to cloud storage. User can also edit their earlier posted messages any number of times.


# Tech-stack for application development

* Python with Flask
* Javascript and JQuery 3.x.x
* Bootstarp 5.x.x

# Challenges Faced


* Managing service accounts credentials to manage app access to the cloud platform.
* Uploading file to Google App Engine - Read Only FS error occured which was resolved by uploading files to /tmp/ folder
* Securing the credentials files

# Deployment Guide

1. Clone the repository

2. Getting service accounts credentials - Firebase

    * Create a firebase project and add an web application to that project.
    * Download the credentials json file from project settings -> service accounts. Read more about adding the Firebase Admin SDK to your server - https://firebase.google.com/docs/admin/setup
    * Move this file to "application_folder/config/" as "forum-firebase-project-firebase-adminsdk-6imbv-9e7b32d5b3.json"
    
3. Getting service accounts credentials - Firebase
 
    * Go to Google Cloud Console and create a project
    * Go to IAM & Admin -> Service Accounts -> Create service account -> Give appropriate name and descrpiption
    * Select Role -> Basic -> Owner. 
    * Hit Continue -> Hit Done
    * Note: Alternatively you can provide specific role to each service account for using specific services such as Cloud Storage, BigQuery etc.
    * Select service account -> Manage keys -> Add key -> Download the credentials JSON file.
    * Move this file to "application_folder/config/" as "forum-google-cloud-service-account.json"

4. Setting up Cloud Storage
   * Select cloud storage -> create bucket (Alternatively you can use existing bucket)
   * Provide appropricate bucket name, and Select Region. 
   * Make sure to change the Access control policy to Fine Grained
   * Create the bucket by keeping other settings to default.


5. Updating config.py
   * Config file is located as /application_folder/config/config file
   ```
   config = {
    "application": {
        "base_url": "http://localhost:3000/",
        "upload_folder": './uploads',
        "allowed_extensions": {'.png', '.jpg', '.jpeg', '.gif'},
        "secret_key": "YOUR-SECRET-KEY"
    },
    "database": {

    },
    "google_cloud":{
        "bucket_name": "YOUR-BUCKET-NAME"
    }
   }
   ```
6. Install dependancies
   ```
   pip install -r requirements.txt

   ```

7. Run application using python main.py



# Resources

[1] - Setting up firebase database authentication
Add the Firebase Admin SDK to your server
Add the Firebase Admin SDK to your server (2021). Available at: https://firebase.google.com/docs/admin/setup (Accessed: 9 March 2021).

[2] - Authenticating google cloud storage
Authenticating as a service account  |  Authentication  |  Google Cloud
Authenticating as a service account  |  Authentication  |  Google Cloud (2021). Available at: https://cloud.google.com/docs/authentication/production (Accessed: 7 April 2021).

[3] - Setting global context processor
Templates — Flask Documentation (1.1.x)
Templates — Flask Documentation (1.1.x) (2021). Available at: https://flask.palletsprojects.com/en/1.1.x/templating/ (Accessed: 9 March 2021).

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

[8] - Important resource for deployment guide
https://www.freecodecamp.org/news/how-to-build-a-web-application-using-flask-and-deploy-it-to-the-cloud-3551c985e492/

[13] - Authenticating with a service account key file  |  BigQuery
Authenticating with a service account key file  |  BigQuery (2021). Available at: https://cloud.google.com/bigquery/docs/authentication/service-account-file (Accessed: 7 April 2021).

