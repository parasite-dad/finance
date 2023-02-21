import os
from pickle import TRUE
import re
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)
app.config['ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TESTING'] = True

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# uri = os.getenv("DATABASE_URL")
# if uri.startswith("postgres://"):
#     uri = uri.replace("postgres://", "postgresql://")
# db = SQL(uri)

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show portfolio of stocks"""
    if request.method == "GET":
        # BELOW SQL NOT GOOD COMPARE TO STAFF SQL, IT IS GROUP BY AND POSTRES AND SQLITE SYSNTAX SEEMS A BIT DIFFERENCE, GROUP BY NEEDED AGAIN stockname, stocksymbol and cannot select stockprice, totalvalue
        dbtransactions = db.execute(
            "SELECT stockname,stocksymbol,sum(case when type=FALSE then stockqty-2*stockqty else stockqty end) as stockqty FROM transactions WHERE userid=? GROUP BY stockname,stocksymbol;", session["user_id"])

        if dbtransactions is None:
            print("1none")
        dbusers = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"])
        rowtransactions = []
        assetbalance = dbusers[0]['cash']
        totalstockvalue = 0

        # AMEND CODE
        for x in range(len(dbtransactions)):
            currentstockinfo = lookup(dbtransactions[x]["stocksymbol"])
            dbtransactions[x]["stockprice"] = usd(currentstockinfo["price"])
            dbtransactions[x]["totalprice"] = currentstockinfo["price"] * \
                dbtransactions[x]["stockqty"]
            assetbalance = assetbalance + dbtransactions[x]["totalprice"]
            dbtransactions[x]["totalprice"] = usd(
                dbtransactions[x]["totalprice"])
            rowtransactions.append(dbtransactions[x])
        totalstockvalue = assetbalance-dbusers[0]['cash']

        return render_template("index.html", clientname=dbusers[0]['username'], transactions=rowtransactions, assetbalance=usd(assetbalance), cashbalance=usd(dbusers[0]['cash']), totalvalue=usd(totalstockvalue))
    # POST METHOD
    else:
        if int(request.form.get("shares")) < int(0):
            return apology("Number of Shares needed greater than 0", 403)
    # THIS IS BUY ACTION METHOD
        if request.form["submit_btn"] == "buy":
            if not request.form.get("shares"):
                return apology("must provide qty to sell", 403)
        # REDIRECT METHOD AND PASSING TWO VARIABLE
            return redirect(url_for('buy', symbol=request.form.get("symbol"), shares=request.form.get("shares")))
    # THIS IS SELL ACTION METHOD
        if request.form["submit_btn"] == "sell":
            if not request.form.get("shares"):
                return apology("must provide qty to sell", 403)
        # REDIRECT METHOD AND PASSING TWO VARIABLE url_for
            return redirect(url_for('sell', symbol=request.form.get("symbol"), shares=request.form.get("shares")))


@ app.route("/buy", methods=["GET", "POST"])
@ app.route("/buy?<symbol><shares>", methods=["GET"])
@ login_required
def buy():
    """Buy shares of stock"""
    # POST METHOD
    if request.method == "POST":
        if not request.form.get("symbol") or not request.form.get("shares"):
            return apology("must provide symbol/qty", 400)
        else:
            symbolrequest = request.form.get("symbol")
            sharesrequest = request.form.get("shares")
    # SELL METHOD
    elif request.method == "GET":
        if request.args.get("symbol") is None:
            dbrows = db.execute(
                "SELECT * FROM users WHERE id = ?", session["user_id"])
            return render_template("buy.html", clientname=dbrows[0]['username'], name="", price="", symbol="", shares="", balance=usd(dbrows[0]['cash']))
        else:
            print(session["user_id"])
            print(request.args.get("symbol"))
            print(request.args.get("shares"))
            symbolrequest = request.args.get("symbol")
            sharesrequest = request.args.get("shares")

    rows = lookup(symbolrequest)
    if rows == None:
        return apology("Cannot find this company!", 400)
    isfloat = True
    if not stringtofloat(sharesrequest):
        return apology("Number of Shares needed integer and no character and greater than 0", 400)
    else:
        dbrows = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"])
        # print("shares:")
        # print(type(request.form.get("shares")))
        # print(float(request.form.get("shares")))
        shares1 = int(float(sharesrequest))
        if float(dbrows[0]['cash']) < float(rows['price'])*shares1:
            return apology("Not enough cash to buy this shares", 400)
        else:
            db.execute("INSERT INTO transactions (userid, stockname, stocksymbol, stockprice, stockqty, totalprice,type) VALUES (?,?,?,?,?,?,?)",
                       session["user_id"], rows['name'], rows['symbol'], rows['price'], shares1, rows['price']*shares1, 'TRUE')
            db.execute("UPDATE users SET cash=? WHERE id=?",
                       float(dbrows[0]['cash']-rows['price'] * shares1), session["user_id"])
            dbrows = db.execute(
                "SELECT * FROM users WHERE id = ?", session["user_id"])
            # return render_template("buy.html", clientname=dbrows[0]['username'], name=rows['name'], price=usd(rows['price']), symbol=rows['symbol'], shares=shares1, balance=usd(dbrows[0]['cash']))
            # FLASH THE MSG TO HTML
            flash('Stock were successfully bought')
            return redirect("/")

# CHECK THE STRING INPUT WHETHER VALID OR NOT, STRING ACCEPT FLOAT, HOW TO MAKE?? DIFFICULT


def stringtofloat(text):

    textlen = len(text)
    splittext = re.split("\.", text)
    if len(splittext) != 1:
        for x in range(len(splittext)):
            if not splittext[x].isdigit():
                return False
        if int(splittext[1]) == int(0):
            return True
        else:
            return False
    else:
        if text.isdigit():
            return True
        else:
            return False


@ app.route("/history")
@ login_required
def history():
    """Show history of transactions"""

    if request.method == "GET":
        dbtransactions = db.execute(
            "SELECT id, userid, stockname, stockprice, stockqty, stocksymbol, time, totalprice, (CASE when type=FALSE then 'SELL' ELSE 'BUY' END) AS type FROM transactions WHERE userid = ? ORDER BY time ASC", session["user_id"])
        dbusers = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"])
        for x in range(len(dbtransactions)):
            dbtransactions[x]['stockprice'] = usd(
                dbtransactions[x]['stockprice'])
            dbtransactions[x]['totalprice'] = usd(
                dbtransactions[x]['totalprice'])
    return render_template("history.html", clientname=dbusers[0]['username'], transactions=dbtransactions, cashbalance=usd(dbusers[0]['cash']), transactioncount=len(dbtransactions))
    return apology("TODO")


@ app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@ app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@ app.route("/quote", methods=["GET", "POST"])
@ login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must provide symbol", 400)
        rows = lookup(request.form.get("symbol"))
        if rows != None:
            return render_template("quoted.html", name=rows['name'], price=usd(rows['price']), symbol=rows['symbol'])
        else:
            return apology("Cannot find this company!", 400)
    else:
        return render_template("quote.html")


@ app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    render_template("register.html")
    if request.method == "POST":
        # CHECK THE PASSWORD IS ALL NUMBER OR NOT AND AT LEAST ONE CHARACTER
        if request.form.get("password").isdigit():
            return apology("password and confirmed passoword needed the at least one character", 400)
        else:
            # CHECK CONFIRMATION PASSWORD AND NEW PASSWORD MATCHED
            if not request.form.get("username"):
                return apology("must provide username", 400)
            elif not request.form.get("password"):
                return apology("must provide password", 400)
            elif not request.form.get("confirmation"):
                return apology("must provide confirmed password", 400)
            if request.form.get("password") != request.form.get("confirmation"):
                return apology("password and confirmed passoword needed the same", 400)
            print(type(request.form.get("password")))

            # Query database for username
            rows = db.execute("SELECT * FROM users WHERE username = ?",
                              request.form.get("username"))
            if len(rows) == 0:
                name = request.form.get("username")
    # GENERATE A HASH
                passwordhash = generate_password_hash(
                    request.form.get("password"))
                db.execute("INSERT INTO users (username, hash) VALUES(?, ?)",
                           name, passwordhash)
                rows = db.execute("SELECT * FROM users WHERE username = ?",
                                  request.form.get("username"))
                session["user_id"] = rows[0]["id"]
                flash('You were successfully registered')
                return redirect("/")
            else:
                return apology("this username already registered, please use another username", 400)
    else:
        return render_template("register.html")
    # return apology("TODO")


@ app.route("/sell", methods=["GET", "POST"])
@ app.route("/sell?<symbol><shares>", methods=["GET"])
@ login_required
def sell():
    # BELOW IS SELL CODE WITH FUNCTION SHOWING ALL THE EXISTING STOCK BUT TROUBLESOME AND STUPID CODE BECAUSE OF THE STUPID SQL, STAFF SQL IS GOOD
    # SEEL BY POST
    if request.method == "POST":
        if not request.form.get("symbol") or not request.form.get("shares"):
            return apology("must provide symbol/qty", 400)
        symbolrequest = request.form.get("symbol")
        sharesrequest = request.form.get("shares")
    # SELL BY GET FROM THE INDEX PAGE
    elif request.method == "GET" and request.args.get("symbol") and request.args.get("shares"):
        symbolrequest = request.args.get("symbol")
        sharesrequest = request.args.get("shares")
    # JUST NORMAL GET
    else:
        # dbtransactions = db.execute(
        #     "SELECT stockname,stocksymbol ,stockprice, totalprice,sum(case when type=FALSE then stockqty-2*stockqty else stockqty end) as stockqty FROM transactions WHERE userid=? GROUP BY stocksymbol;", session["user_id"])
        dbtransactions = db.execute(
            "SELECT stockname,stocksymbol ,sum(case when type=FALSE then stockqty-2*stockqty else stockqty end) as stockqty FROM transactions WHERE userid=? GROUP BY stockname,stocksymbol;", session["user_id"])

        if dbtransactions is None:
            print("1none")
        dbusers = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"])
        rowtransactions = []
        assetbalance = dbusers[0]['cash']
        totalstockvalue = 0
        # print(dbtransactions[0]['stockqty'])

        for x in range(len(dbtransactions)):
            currentstockinfo = lookup(dbtransactions[x]["stocksymbol"])
            dbtransactions[x]["stockprice"] = usd(currentstockinfo["price"])
            dbtransactions[x]["totalprice"] = currentstockinfo["price"] * \
                dbtransactions[x]["stockqty"]
            assetbalance = assetbalance + dbtransactions[x]["totalprice"]
            dbtransactions[x]["totalprice"] = usd(
                dbtransactions[x]["totalprice"])
            rowtransactions.append(dbtransactions[x])
        totalstockvalue = assetbalance-dbusers[0]['cash']
        return render_template("sell.html", clientname=dbusers[0]['username'], transactions=rowtransactions, cashbalance=usd(dbusers[0]['cash']), totalvalue=usd(totalstockvalue))
    # ACTUAL SELL PROCEDURE
    currentstockinfo = lookup(symbolrequest.upper())
    if currentstockinfo == None:
        return apology("Cannot find this company!", 400)
    dbtransactions = db.execute(
        "SELECT stockname,stocksymbol ,sum(case when type=FALSE then stockqty-2*stockqty else stockqty end) as stockqty FROM transactions WHERE userid=? AND stocksymbol=? GROUP BY stockname,stocksymbol;", session["user_id"], symbolrequest)
    rowtransactions = []
    print(dbtransactions)
    print(type(dbtransactions[0]["stockqty"]))
    position = 0

    if int(sharesrequest) < int(0) or dbtransactions[position]['stockqty'] < int(sharesrequest):
        return apology("Number of Shares needed greater than 0 or You cannot sell qty more than you have", 400)
    else:
        dbrows = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"])
        db.execute("INSERT INTO transactions (userid, stockname, stocksymbol, stockprice, stockqty, totalprice,type) VALUES (?,?,?,?,?,?,?)",
                   session["user_id"], currentstockinfo['name'], currentstockinfo['symbol'], currentstockinfo['price'], float(sharesrequest), float(currentstockinfo['price'])*float(sharesrequest), 'FALSE')
        db.execute("UPDATE users SET cash=? WHERE id=?",
                   float(dbrows[0]['cash'])+float(currentstockinfo['price'])*float(sharesrequest), session["user_id"])
        flash('Stock were successfully sold')
        return redirect("/")


@ app.route("/setting", methods=["GET", "POST"])
# @ login_required
def setting():
    # ADD THIS NEW FUNCTION TO CHANGE PWD AND ADD CASH
    render_template("setting.html")
    if request.method == "POST":
        # TODO: Add the user's entry into the database
        # print(request.form["changepwd"])
        # CAN SELECT BASED ON FORM BUTTON, CHANGE PWD
        if request.form["formbutton"] == "changepwd":
            # print(request.form["formbutton"])
            if not request.form.get("username"):
                return apology("must provide username", 403)
            elif not request.form.get("oldpassword"):
                return apology("must provide Old password", 403)
            elif not request.form.get("newpassword"):
                return apology("must provide New password", 403)
            elif not request.form.get("confirmation"):
                return apology("must provide confirmed password", 403)
            if request.form.get("newpassword") != request.form.get("confirmation"):
                return apology("New password and confirmed passoword needed the same", 403)
            # Query database for username
            rows = db.execute("SELECT * FROM users WHERE username = ? AND id=?",
                              request.form.get("username"), session["user_id"])
            # session["user_id"] = rows[0]["id"]
            if len(rows) == 0:
                return apology("This username is not existed or it is not your account", 403)
            else:
                if not check_password_hash(rows[0]["hash"], request.form.get("oldpassword")):
                    return apology("invalid username and/or password", 403)
                passwordhash = generate_password_hash(
                    request.form.get("newpassword"))
                db.execute("UPDATE users SET hash=? WHERE id=?",
                           passwordhash, session["user_id"])
                # Redirect user to home page
                return redirect("/")
        # FORM BUTTON ADD CASH
        elif request.form["formbutton"] == "addcash":
            # else:
            # print(request.form["formbutton"])
            if not request.form.get("password"):
                return apology("must provide password", 403)
            elif not request.form.get("cashadd") or float(request.form.get("cashadd")) < 0:
                return apology("must provide cash amount and positive amount ", 403)
            rows = db.execute(
                "SELECT * FROM users WHERE id=?", session["user_id"])
            if not check_password_hash(rows[0]["hash"], request.form.get("password")):
                return apology("invalid password", 403)
            db.execute("UPDATE users SET cash=? WHERE id=?",
                       float(rows[0]["cash"])+float(request.form.get("cashadd")), session["user_id"])
            return redirect("/")
    else:
        return render_template("setting.html")
