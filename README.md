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

