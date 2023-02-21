from flask import Flask, redirect, url_for, render_template, request, session
import pyrebase
import json
import firebase_admin
from firebase_admin import auth as _auth, db

def remove_from_profile(url, branch):
    ref2 = db.reference(sanitize_email(session["details"]["email"]))
    d = ref2.get()
    d[branch].remove(url)
    ref2.update({branch: d[branch]})

def add_to_profile(url, branch):
    ref2 = db.reference(sanitize_email(session["details"]["email"]))
    d = ref2.get()
    if d != None:
        if branch in d:
            d[branch].append(url)
            ref2.update({branch: d[branch]})
        else:
            d = {}
            d[branch] = [url]
            ref2.update({branch: d[branch]})
    else:
        d = {}
        d[branch] = [url]
        ref2.set({branch: d[branch]})

def sanitize_email(email):
    return email.replace("@", "-at-").replace(".", "-dot-")

# Setting up firebase
cred_obj = firebase_admin.credentials.Certificate('json.json')
default_app = firebase_admin.initialize_app(cred_obj, {
	'databaseURL': ""
})

# Setting up firebase
config = {
  "apiKey": "",
  "authDomain": "",
  "databaseURL": "",
  "storageBucket": "",
  "serviceAccount": ""
}
firebase = pyrebase.initialize_app(config)
auth = firebase.auth()

app = Flask(__name__)

# Change this
app.secret_key = "JSAHDKQDS hfvw]vwd[[vwd}vwdnrrwdvwvdvdve[]][wdvwdv{efbvwdvngb[{]>SAD24G4EF<1WW8WU9}:WQED12388123123~!~)@>kDS"
@app.route("/")
def home():
    if "details" in session:
        if "username" not in session["details"]:
            loggedIn = False
        else:
            loggedIn = True
    else:
        loggedIn = False
    get = db.reference("/").get()
    try:
        total = [(i, get[i]) for i in get if "at" not in i]
    except:
        total = []
    return render_template("index.html", loggedIn=loggedIn, all=total)

@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session["details"] = {"username": user["displayName"], "email": email}
            return redirect(url_for("home"))
        except Exception as e:
            try:
                user = _auth.create_user(
                    email = email,
                    display_name = name,
                    password = password
                )
                session["details"] = {"username": name, "email": email}
                return redirect(url_for("home"))
            except Exception as e:
                return render_template("login.html", alert=e)
    return render_template("login.html", alert="")

@app.route("/create/", methods=["GET", "POST"])
def create():
    options = ["Windows 10 & 11", "MacOS", "Debian-based", "Arch-based"]
    options1 = ["Powershell", "Bash", "Z Shell"]
    if "details" in session:
        if "username" not in session["details"]:
            session.clear()
            return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))
    if request.method == "POST":
        name = request.form["name"]
        currLevel = 0
        last = ""
        obj = {}
        for i in request.form:
            if i == "name":
                continue
            split = i.split("-")
            if "command" in i:
                currLevel = split[0]
                obj[request.form[i]] = {"os": [], "shells": []}
                last = request.form[i]
            elif "shcbox" in i:
                obj[last]["shells"].append(options1[int(split[0])])
            elif "oscbox" in i:
                obj[last]["os"].append(options[int(split[0])])
        toDel = []
        for i in obj:
            if i == "": toDel.append(i)
            else:
                if obj[i]["os"] == [] or obj[i]["shells"] == []:
                    toDel.append(i)
        for i in toDel:
            del obj[i]
        if len(obj) == 0:
            return render_template("create.html", loggedIn=session["details"])
        ref = db.reference("/").push()
        ref.set({
            "name": name,
            "obj": obj,
            "by": session["details"]["username"]
        })
        url = ref._pathurl[1::]
        add_to_profile(url, "created")
        return redirect(url_for("choice", url=url))
    return render_template("create.html", loggedIn=session["details"])

@app.route("/choice/<url>/", methods=["GET", "POST"])
def choice(url):
    if "details" in session:
        if "username" not in session["details"]:
            loggedIn = False
        else:
            loggedIn = True
    else:
        loggedIn = False
    if request.method == "POST" and "details" in session:
        ref = db.reference(url)
        data = db.reference(url).get()
        if data == None: return redirect(url_for("home"))
        if "cast-by" in data:
            castby = data["cast-by"]
            if session["details"]["email"] in castby:
                castby.remove(session["details"]["email"])
                data["stars"] -= 1
                remove_from_profile(url, "starred")
            else:
                data["stars"] += 1
                castby.append(session["details"]["email"])
                add_to_profile(url, "starred")
        else:
            castby = [session["details"]["email"]]
            data["stars"] = 1
            add_to_profile(url, "starred")
        ref.update({"stars": data["stars"]})
        ref.update({"cast-by": castby})
    try:
        data = db.reference(url).get()
    except:
        return redirect(url_for("home"))
    contains = False
    try:
        if "cast-by" in data:
            if session["details"]["email"] in data["cast-by"]:
                contains = True
    except:
        pass
    s = "s"
    if data == None: return redirect(url_for("home"))
    if "stars" in data:
        stars = data["stars"]
        if stars == 1: s = ""
    else:
        stars = 0
    return render_template("choice.html", data=data, contains=contains, loggedIn=loggedIn, stars=stars, s=s)

@app.route("/logout/")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/profile/")
def profile():
    if "details" in session:
        if "username" not in session["details"]:
            session.clear()
            return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))
    ref = db.reference(sanitize_email(session["details"]["email"]))
    d = ref.get()
    if d == None:
        ress = []
        resc = []
    else:
        if "starred" in d:
            ress = d["starred"]
        else:
            ress = []
        if "created" in d:
            resc = d["created"]
        else:
            resc = []
    ress2 = ress.copy()
    resc2 = resc.copy()
    ress = {}
    resc = {}
    for i in ress2:
        ref2 = db.reference(i)
        dd = ref2.get()
        ress[dd["name"]] = i
    for i in resc2:
        ref2 = db.reference(i)
        dd = ref2.get()
        resc[dd["name"]] = i
    return render_template("profile.html", loggedIn=session["details"], username=session["details"]["username"], email=session["details"]["email"], starred=ress, created=resc)

if __name__ == "__main__":
	app.run(debug=True)