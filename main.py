from flask import Flask, render_template, jsonify, request
from config.config import config

app = Flask(__name__)

# Defining a contex so that global variables can be accessed in the templates
@app.context_processor
def get_global_config():
  return {"config": config}

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods = ['GET'])
def login_get():
    return render_template("login.html")


@app.route("/login", methods = ['POST'])
def login_post():
    
    id = request.form['id']
    password = request.form['password']

    # call firebase and validate this details with stored data

    if True :
        res = { "status" : "success"}
    else :
        res = { "status" : "failed"}

    return jsonify(res)


@app.route("/register", methods = ['GET'])
def register_get():
    return render_template("register.html")


@app.route("/register", methods = ['POST'])
def register_post():
    return "register_post"


    
if __name__ == "__main__":
    app.run(debug=True)