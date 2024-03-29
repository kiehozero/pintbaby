import os
from flask import (
    Flask, flash, render_template, redirect, request, session, url_for)
from flask_pymongo import PyMongo
from werkzeug.security import (
    generate_password_hash, check_password_hash)
from bson.objectid import ObjectId
if os.path.exists("env.py"):
    import env


app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/add_pub", methods=["GET", "POST"])
def add_pub():
    if not session.get("user"):
        return redirect(url_for('error_handler'))
    countries = mongo.db.countries.find().sort("name")
    if request.method == "POST":
        new_pub = {
            "pname": request.form.get("pname"),
            "loc": request.form.get("loc"),
            "city": request.form.get("city"),
            "state": request.form.get("state"),
            "country": request.form.get("country"),
            "photo": request.form.get("photo")
        }

        mongo.db.pubs.insert_one(new_pub)
        # uses form entry to get pub_id, then passes to redirect
        pub_id = mongo.db.pubs.find_one(
            {"pname": format(request.form.get("pname"))})["_id"]
        flash("{} successfully added".format(request.form.get("pname")))
        return redirect(url_for('add_review_of', pub_id=pub_id))

    # GET method
    return render_template("add_pub.html", countries=countries)


@app.route("/add_review", methods=["GET", "POST"])
def add_review():
    if not session.get("user"):
        return redirect(url_for('error_handler'))
    # this function only routes to the pub page, unlike add_review_of
    pubs = mongo.db.pubs.find().sort("pname")
    if request.method == "POST":
        new_review = {
            "pub": request.form.get("pub"),
            "visit": request.form.get("visit"),
            "prating": request.form.get("prating"),
            "drating": request.form.get("drating"),
            "arating": request.form.get("arating"),
            "price": request.form.get("price"),
            "review": request.form.get("review"),
            "author": session["user"]
        }
        # uses form entry to get pub _id, then passes to redirect
        pub_ref = mongo.db.pubs.find_one(
            {"pname": format(request.form.get("pub"))})["_id"]

        mongo.db.reviews.insert_one(new_review)
        flash("Review of {} added".format(request.form.get("pub")))
        return redirect(url_for('view_pub', pub_id=pub_ref))

    # GET method
    return render_template("add_review.html", pubs=pubs)


@app.route("/add_review_of/<pub_id>", methods=["GET", "POST"])
def add_review_of(pub_id):
    if not session.get("user"):
        return redirect(url_for('error_handler'))
    # this function routes to and from a pub's page
    pub_id = mongo.db.pubs.find_one(
        {"_id": ObjectId(pub_id)})
    if request.method == "POST":
        new_review = {
            "pub": request.form.get("pub"),
            "visit": request.form.get("visit"),
            "prating": request.form.get("prating"),
            "drating": request.form.get("drating"),
            "arating": request.form.get("arating"),
            "price": request.form.get("price"),
            "review": request.form.get("review"),
            "author": session["user"]
        }
        # uses form entry to get pub _id, then passes to redirect
        pub_ref = mongo.db.pubs.find_one(
            {"pname": format(request.form.get("pub"))})["_id"]

        mongo.db.reviews.insert_one(new_review)
        flash("Review Added")
        return redirect(url_for('view_pub', pub_id=pub_ref))

    # GET method
    return render_template(
        "add_review_of.html", pub_id=pub_id)


@app.route("/contact_us")
def contact_us():
    if request.method == "POST":
        flash("E-mail sent!")
    return render_template("contact_us.html")


@app.route("/delete_pub_admin/<pub_id>")
# admin-only function to delete a pub
def delete_pub_admin(pub_id):
    if not session.get("user"):
        return redirect(url_for('error_handler'))
    if not session["user"] == "pbadmin":
        return redirect(url_for('error_handler'))
    mongo.db.pubs.remove(
        {"_id": ObjectId(pub_id)}
    )
    flash("Pub Deleted")
    return redirect(url_for('pubs'))


@app.route("/delete_review/<review_id>")
def delete_review(review_id):
    if not session.get("user"):
        return redirect(url_for('error_handler'))
    mongo.db.reviews.remove(
        {"_id": ObjectId(review_id)}
    )
    flash("Review Deleted")
    return redirect(url_for(
        'my_reviews', username=session["user"]))


@app.route("/delete_review_admin/<review_id>")
# admin-only function, deletes reviews
# routing to and from pub page
def delete_review_admin(review_id):
    if not session.get("user"):
        return redirect(url_for('error_handler'))
    if not session["user"] == "pbadmin":
        return redirect(url_for('error_handler'))
    # uses review _id to find pub name, then passes pub _id to redirect
    review = mongo.db.reviews.find_one(
        {"_id": ObjectId(review_id)})
    pub_id = mongo.db.pubs.find_one(
        {"pname": format(review["pub"])})["_id"]
    mongo.db.reviews.remove(
        {"_id": ObjectId(review_id)}
    )
    flash("Review Deleted")
    return redirect(url_for('view_pub', pub_id=pub_id))


@app.route("/delete_review_admin_user/<review_id>")
# admin-only function, deletes reviews
# routing to and from the admin user panel
def delete_review_admin_user(review_id):
    if not session.get("user"):
        return redirect(url_for('error_handler'))
    if not session["user"] == "pbadmin":
        return redirect(url_for('error_handler'))
    # uses review _id to find user name, then passes user _id to redirect
    review = mongo.db.reviews.find_one(
        {"_id": ObjectId(review_id)})
    user_id = mongo.db.users.find_one({"username": review["author"]})["_id"]
    mongo.db.reviews.remove(
        {"_id": ObjectId(review_id)}
    )
    flash("Review Deleted")
    return redirect(url_for('moderate_user', user_id=user_id))


@app.route("/delete_user/<user_id>")
def delete_user(user_id):
    if not session.get("user"):
        return redirect(url_for('error_handler'))
    if not session["user"] == "pbadmin":
        return redirect(url_for('error_handler'))
    # admin-only function to delete accounts
    mongo.db.users.remove(
        {"_id": ObjectId(user_id)}
    )
    flash("User Deleted")
    return redirect(url_for('users'))


@app.route("/edit_profile/<username>", methods=["GET", "POST"])
def edit_profile(username):
    if not session.get("user"):
        return redirect(url_for('error_handler'))
    if request.method == "POST":
        user_id = mongo.db.users.find_one({"username": session["user"]})["_id"]
        mongo.db.users.update(
            # Bugfix #3: set parameter in update function
            {"_id": user_id}, {"$set": {
                "username": request.form.get("username"),
                "first_name": request.form.get("first_name"),
                "last_name": request.form.get("last_name"),
                "email": request.form.get("email")
                }
            }
        )

        flash("Profile Updated")
        return redirect(url_for(
            'my_reviews', username=session["user"]))

    # GET method
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    user = mongo.db.users.find_one(
        {"username": session["user"]})
    user_id = mongo.db.users.find_one(
        {"username": session["user"]})["_id"]
    return render_template(
        "edit_profile.html", username=username, user=user, user_id=user_id)


@app.route("/edit_pub/<pub_id>", methods=["GET", "POST"])
def edit_pub(pub_id):
    if not session.get("user"):
        return redirect(url_for('error_handler'))
    if not session["user"] == "pbadmin":
        return redirect(url_for('error_handler'))
    if request.method == "POST":
        edited_pub = {
            "pname": request.form.get("pname"),
            "loc": request.form.get("loc"),
            "city": request.form.get("city"),
            "state": request.form.get("state"),
            "country": request.form.get("country"),
            "photo": request.form.get("photo")
        }
        mongo.db.pubs.update(
            {"_id": ObjectId(pub_id)}, edited_pub)
        flash("Pub Amended")
        return redirect(url_for('view_pub', pub_id=pub_id))

    # GET method
    pub = mongo.db.pubs.find_one({"_id": ObjectId(pub_id)})
    countries = mongo.db.countries.find().sort("name")
    return render_template(
        "edit_pub.html", pub=pub, countries=countries)


@app.route("/edit_review/<review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    if not session.get("user"):
        return redirect(url_for('error_handler'))
    if request.method == "POST":
        edited_review = {
            "pub": request.form.get("pub"),
            "visit": request.form.get("visit"),
            "prating": request.form.get("prating"),
            "drating": request.form.get("drating"),
            "arating": request.form.get("arating"),
            "price": request.form.get("price"),
            "review": request.form.get("review"),
            "author": session["user"]
        }
        mongo.db.reviews.update(
            {"_id": ObjectId(review_id)}, edited_review)
        flash("Review Amended")
        return redirect(url_for(
            'my_reviews', username=session["user"]))

    # GET method
    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    pubs = mongo.db.pubs.find().sort("pname")
    return render_template(
        "edit_review.html", review=review, pubs=pubs)


@app.route("/error_handler")
def error_handler():
    return render_template("error_handler.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # username validation
        is_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        if is_user:
            # password match
            if check_password_hash(
                is_user["password"], request.form.get(
                    "password")):
                session["user"] = request.form.get("username").lower()
                return redirect(url_for(
                    'my_reviews', username=session["user"]))

            else:
                flash("Username and password combination is incorrect")
                return redirect(url_for('login'))

        else:
            flash("Username and password combination is incorrect")
            return redirect(url_for('login'))

    # GET method
    return render_template("login.html")


@app.route("/logout")
def logout():
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for('login'))


@app.route("/moderate_review/<review_id>", methods=["GET", "POST"])
# admin-only function to moderate content, e.g. offensive or legally
# questionable statements. This route begins and ends at the pub's page
def moderate_review(review_id):
    if not session.get("user"):
        return redirect(url_for('error_handler'))
    if not session["user"] == "pbadmin":
        return redirect(url_for('error_handler'))
    if request.method == "POST":
        edited_review = {
            "pub": request.form.get("pub"),
            "visit": request.form.get("visit"),
            "prating": request.form.get("prating"),
            "drating": request.form.get("drating"),
            "arating": request.form.get("arating"),
            "price": request.form.get("price"),
            "review": request.form.get("review"),
            "author": request.form.get("author")
        }
        pub_id = mongo.db.pubs.find_one(
            {"pname": format(request.form.get("pub"))})["_id"]
        mongo.db.reviews.update(
            {"_id": ObjectId(review_id)}, edited_review)
        flash("Review Amended")
        return redirect(url_for('view_pub', pub_id=pub_id))

    # GET method
    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    pubs = mongo.db.pubs.find().sort("pname")
    return render_template(
        "moderate_review.html", review=review, pubs=pubs)


@app.route("/moderate_review_user/<review_id>", methods=["GET", "POST"])
# Same as moderate_review above but routes from
# user profile and back to same profile on POST
def moderate_review_user(review_id):
    if not session.get("user"):
        return redirect(url_for('error_handler'))
    if not session["user"] == "pbadmin":
        return redirect(url_for('error_handler'))
    if request.method == "POST":
        edited_review = {
            "pub": request.form.get("pub"),
            "visit": request.form.get("visit"),
            "prating": request.form.get("prating"),
            "drating": request.form.get("drating"),
            "arating": request.form.get("arating"),
            "price": request.form.get("price"),
            "review": request.form.get("review"),
            "author": request.form.get("author")
        }
        user_id = mongo.db.users.find_one(
            {"username": format(request.form.get("author"))})["_id"]
        mongo.db.reviews.update(
            {"_id": ObjectId(review_id)}, edited_review)
        flash("Review amended")
        return redirect(url_for('moderate_user', user_id=user_id))

    # GET method
    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    pubs = mongo.db.pubs.find().sort("pname")
    return render_template(
        "moderate_review_user.html", review=review, pubs=pubs)


@app.route("/moderate_user/<user_id>")
# admin-only function to search for reviews by user and moderate them
def moderate_user(user_id):
    if not session.get("user"):
        return redirect(url_for('error_handler'))
    if not session["user"] == "pbadmin":
        return redirect(url_for('error_handler'))
    mod_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    user = mod_user["username"]
    reviews = list(mongo.db.reviews.find(
        {"author": mod_user["username"]}
        ))
    return render_template(
        "moderate_user.html", user_id=user_id, reviews=reviews, user=user)


@app.route("/my_reviews/<username>", methods=["GET", "POST"])
def my_reviews(username):
    if not session.get("user"):
        return redirect(url_for('error_handler'))

    if session["user"]:
        # only returns username from MongoDB users collection
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]
        # returns reviews by active user, ordered by most recent visit first
        reviews = list(mongo.db.reviews.find(
            {"author": session["user"]}).sort("visit", -1))
        return render_template(
            "my_reviews.html", username=username, reviews=reviews)
    # At the moment this just loads a Jinja error
    return redirect(url_for('login'))


@app.route("/pubs")
def pubs():
    # Converting below to a list allows the if loop in the template
    # page to work properly when a user searches for somewhere
    pubs = list(mongo.db.pubs.find().sort("pname"))
    return render_template("pubs.html", pubs=pubs)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # username validation
        is_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        if is_user:
            flash("Username taken!")
            return redirect(url_for('register'))

        reg_user = {
            "username": request.form.get("username").lower(),
            "first_name": request.form.get("first_name").lower(),
            "last_name": request.form.get("last_name").lower(),
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }

        mongo.db.users.insert_one(reg_user)

        session["user"] = request.form.get("username").lower()
        # successful log-in re-directs to their new blank profile page
        return redirect(url_for('my_reviews', username=session["user"]))

    # GET method
    return render_template("register.html")


@app.route("/search_pubs", methods=["GET", "POST"])
def search_pubs():
    query = request.form.get("search")
    pubs = list(
        mongo.db.pubs.find({"$text": {"$search": query}}).sort("pname"))
    return render_template("pubs.html", pubs=pubs)


@app.route("/users")
# admin-only function to display all users
def users():
    if not session.get("user"):
        return redirect(url_for('error_handler'))
    if not session["user"] == "pbadmin":
        return redirect(url_for('error_handler'))
    users = list(mongo.db.users.find().sort("username"))
    return render_template("users.html", users=users)


@app.route("/view_pub/<pub_id>")
def view_pub(pub_id):
    pub_id = mongo.db.pubs.find_one(
        {"_id": ObjectId(pub_id)}
    )
    # sorts reviews by most recent first
    reviews = list(mongo.db.reviews.find(
        {"pub": format(pub_id["pname"])}).sort("visit", -1))
    return render_template(
        "view_pub.html", pub_id=pub_id, reviews=reviews)


@app.route("/view_review/<review_id>")
def view_review(review_id):
    review = mongo.db.reviews.find_one(
        {"_id": ObjectId(review_id)}
    )
    # pub is called to display photo
    pub = mongo.db.pubs.find_one(
        {"pname": format(review["pub"])}
    )

    return render_template("view_review.html", review=review, pub=pub)


@app.route("/view_review_admin/<review_id>")
def view_review_admin(review_id):
    review = mongo.db.reviews.find_one(
        {"_id": ObjectId(review_id)}
    )
    user_id = mongo.db.users.find_one(
        {"username": format(review["author"])})["_id"]
    # pub is called to display photo
    pub = mongo.db.pubs.find_one(
        {"pname": format(review["pub"])}
    )

    return render_template(
        "view_review_admin.html", review=review, user_id=user_id, pub=pub)


@app.route("/view_review_user/<review_id>")
def view_review_user(review_id):
    review = mongo.db.reviews.find_one(
        {"_id": ObjectId(review_id)}
    )
    username = mongo.db.users.find_one(
        {"username": format(review["author"])})["username"]
    pub = mongo.db.pubs.find_one(
        {"pname": format(review["pub"])}
    )

    return render_template(
        "view_review_user.html", review=review, username=username, pub=pub)


# Below are all error handlers, courtesy
# of the Pythonise tutorials in the README


@app.errorhandler(403)
def forbidden(e):
    return render_template("error_handler.html"), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("error_handler.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error_handler.html"), 500


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
