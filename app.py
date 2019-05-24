from flask import Flask, render_template,flash, redirect, request, url_for,jsonify,abort,make_response, Response
from decimal import Decimal
from models import *


# from flask_mysqldb import MySQL
from wtforms import Form, StringField, PasswordField, validators, IntegerField, SelectField, SelectMultipleField
# from passlib.hash import sha256_crypt
from functools import wraps
import json
import plotly
import numpy as np
import operator
import sys

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = 'secret'

global events

# Flask App
# app = Flask(__name__, static_url_path='/static')

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'HanSun'
app.config['MYSQL_PASSWORD'] = 'HS2017ucla'
app.config['MYSQL_DB'] = 'mynrha'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = 'ggsimida'

# init MYSQL
# mysql = MySQL(app)

# decimal function
def decimal_default_proc(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


# Index
@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')

# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [
        validators.Length(min=1, max=50),
        validators.input_required()])
    username = StringField('Username', [
        validators.Length(min=4, max=25),
        validators.input_required()])
    email = StringField('Email', [
        validators.Length(min=6, max=50)])
    organization = StringField('Organization', [
        validators.Length(min=1, max=100)])
    password = PasswordField('Password', [
        validators.Length(min=6, max=25),
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


### Refactorrrr!!! Need to make one call so that each page can fill out the appropriate form! (Instead of hard coding it here)
def data_to_tuple(data_in,label_column,prefix="",suffix=""):
    new_array = []
    data_tuple = [tuple(d.values()) for d in data_in]
    for data in data_tuple:
        # print(data)
        if data[0] is not None:
            data_id = data[0]
            data_label = prefix+str(data[label_column])+suffix
            new_array.append([data_id,data_label])
    return new_array

global site_query 
site_query = [site for site in Sites.select().dicts()]
global site_query2
site_query2 = [site for site in Sites.select()]

class RequestForVisualizations(Form):
    
    # site_tuple= [tuple(d.values()) for d in site_query]
    # site_choices = []
    # for site in site_tuple:
    #     site_id = site[0]
    #     site_latlng = "Site #"+str(site[0])
    #     site_choices.append([site_id,site_latlng])
    # site_choices = [value for value in site_choices]
    site_choices = data_to_tuple(site_query,0,prefix="#")

    # print(site_choices)
    # site_choices = dict_to_array(site_query,'idsite')
    earthquake_query = [earthquake for earthquake in Earthquake.select().dicts()]

    building_query = [building for building in Building.select().dicts()]
    building_choices = data_to_tuple(building_query,1,suffix=" Stories")
    earthquake_choices = data_to_tuple(earthquake_query,2)
    # print("site list 50")
    # site_list = dict_to_array(site_query['idsite'].items())
    # earthquake_list = dict_to_array(earthquake_query.items())
    # building_query = dict_to_array(building_query.items())

    # print("building_query")
    # print(building_choices)
    site_select = SelectMultipleField('Site',
                                choices=site_choices,
                                coerce=int
                                )        
    earthquake_select = SelectField('Earthquake',
                            choices=earthquake_choices,
                            coerce=int
                             )

    building_select = SelectField('Building Height',
                           choices=building_choices,
                           coerce=int
                           )

# Request Form Class
# form = RequestForVisualizations(Form)
class RequestFormOpenSeesCMF(Form):
    siteChoice = []
    for i in range(1, 153):
        siteChoice.append((i, str(i)))

    #site = IntegerField('Site, choose from 1-152', [
    #    validators.NumberRange(min=1,max=152),
    #    validators.input_required()])
    site_select = SelectMultipleField('Site',
                                choices=siteChoice,
                                coerce=int
                                )

    earthquake_select = SelectField('Earthquake',
                            choices=[(1, 'Northridge')],
                            coerce=int
                             )
    ### refactor to call from database!!!! ###
    building_select = SelectField('Building Height',
                           choices=[(1, '2 Story'), (2, '4 Story'), (3, '8 Story'), (4, '12 Story'),(5, '20 Story')],
                           coerce=int
                           )

# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        organization = form.organization.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, organization, password) "
                    "VALUES(%s, %s, %s, %s, %s)", (name, email, username, organization, password))
        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']
            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')


# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))

    return wrap


# Logout
@app.route('/logout')
# @is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


# Dashboard
@app.route('/dashboard')
# @is_logged_in
def dashboard():
    return render_template('dashboard.html')


# Visualization CMF
@app.route('/visualizationCMF',methods=['GET', 'POST'])
def visualizationCMF():
    form = RequestForVisualizations(request.form)
    # form = RequestFormOpenSeesCMF(request.form)
    if request.method == 'POST' and form.validate():
        # Get Form Fields
        site = form.site_select.data # site is a list for multiple choices
        earthquake = form.earthquake_select.data
        building = form.building_select.data
        # Create cursor
        # cur = mysql.connection.cursor()

        # Get number of story
        the_building = Building.get(Building.idbuilding == building).idbuilding
        print("the building:")
        #### "Site" in wtf_form "the_building"<--- will refactor ####
        print(the_building)

        # result = cur.execute("SELECT * FROM buildings WHERE idBuilding = %s", [building])
        # buildings = Building.get()
        # level = buildings['level']
        # print the_building

        ### level is from database! ###
        level = (Building.get(Building.idbuilding == the_building).level)
        # print "Building Height"
        # print level
        SDRData = []
        PFAData = []

        # how does level relate to sumSDR??
        # what is sumSDR?

        ### this is used to calculate the average sdr and pfa
        sumSDR = [0]*(level + 1)
        print("sumSDR")
        print(sumSDR)
        sumPFA = [0]*(level + 1)


        
        for iSite in site:
            responses = Response.select().where((Response.idearthquake == earthquake) & (Response.idsite == iSite) & (Response.idbuilding == building))
            PFA = [0.0]
            SDR = [0.0]
            
            for res in responses:
                print("res")
                print(res.sdr)
                SDR.append(float(res.sdr)*100)
                PFA.append(float(res.pfa))

            SDR.reverse
            PFA.reverse
            print("SDR")
            print(SDR)
            print("PFA")
            print(PFA)
            
            # again calculating the average
            sumSDR = [sum(x) for x in zip(sumSDR, SDR)]

            SDRData.append(plotly.graph_objs.Scatter(x=SDR,
                                                     y=list(range(level + 1)),
                                                     name = 'Site-'+str(iSite),
                                                     line = dict(width=1)
                                                     )
                           )


            sumPFA = [sum(x) for x in zip(sumPFA, PFA)]

            PFAData.append(plotly.graph_objs.Scatter(x=PFA,
                                                     y=list(range(level + 1)),
                                                     name='Site-' + str(iSite),
                                                     line=dict(width=1)
                                                     )
                           )


        SDRData.append(plotly.graph_objs.Scatter(x=[ele/len(site) for ele in sumSDR],
                                             y=list(range(level + 1)),
                                             name='Mean',
                                             line=dict(dash='longdash',
                                                       color=('rgb(0, 0, 0)'),
                                                       width=4)
                                                )
                       )

        PFAData.append(plotly.graph_objs.Scatter(x=[ele / len(site) for ele in sumPFA],
                                                 y=list(range(level + 1)),
                                                 name='Mean',
                                                 line=dict(dash='longdash',
                                                           color=('rgb(0, 0, 0)'),
                                                           width=4)
                                                 )
                       )



        graphs = [
            dict(
                data=
                SDRData,
                layout=dict(
                    width=500,
                    height=500,
                    title='Peak Story Drift Ratio of '+str(level)+'-Story Building',
                    xaxis=dict(
                        #range=[0, max([0.5, max(SDR)*1.5])],
                        title='Peak Story Drift Ratio, %',
                        zeroline=True,
                        gridwidth= 2,
                    ),
                    yaxis=dict(
                    title='Story Level',
                    zeroline=True,
                    gridwidth=2,
                    )
                )
            ),

            dict(
                data=
                PFAData,
                layout=dict(
                    width=500,
                    height=500,
                    title='Peak Floor Acceleration of ' + str(level) + '-Story Building',
                    xaxis=dict(
                        #range=[0, max([0.5, max(PFA) * 1.5])],
                        title='Peak Floor Acceleration, g',
                        zeroline=True,
                        gridwidth=2,
                    ),
                    yaxis=dict(
                        title='Story Level',
                        zeroline=True,
                        gridwidth=2,
                    )
                )
            ),
        ]

        # Add "ids" to each of the graphs to pass up to the client for templating
        ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]
        # Convert the figures to JSON
        # PlotlyJSONEncoder appropriately converts pandas, datetime, etc
        # objects to their JSON equivalents
        graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template('plot.html',
                               ids=ids,
                               graphJSON=graphJSON)

    # json_data = jsonify(site_query)
    # return render_template('visualizationCMF.html',form=form)
    site_query_data=json.dumps(site_query, default=decimal_default_proc)
    # print("site_query")
    # print(site_query_data['siteid'])
    return render_template('visualizationCMF.html',form=form,site_query=site_query)

@app.teardown_request
def _db_close(exc):
    if not db.is_closed():
        db.close()

if __name__ == '__main__':
    app.run(debug=True)
