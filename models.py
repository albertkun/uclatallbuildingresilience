# Import from peewee
from peewee import *
from flask import session

# load our config file
from config import Config

# Connect to the PostgresqlDatabase
db = PostgresqlDatabase(database=Config.DATABASE, user=Config.USERNAME, password=Config.SECRET_KEY,
host=Config.HOST, port=Config.PORT)

db.connect()

# class Earthquake(Model):
#     idearthquake = IntegerField(primary_key=True)
#     name = CharField()
#     magnitude = DecimalField()
#     latepc = DecimalField()
#     longepc = DecimalField()
#     date = DateTimeField()

#     class Meta:
#         database = db
#         db_table = 'earthquakes'

class Response(Model):
    idsite = IntegerField(primary_key=True)
    idearthquake = IntegerField()
    idbuilding = IntegerField()
    sdr = DecimalField()
    pfa = DecimalField()
    idresponse = IntegerField()
    class Meta:
        database = db
        db_table = 'responses'

class Building(Model):
    idbuilding = IntegerField(primary_key=True)
    level = IntegerField()
    class Meta:
        database = db
        db_table = 'buildings'    

class Sites(Model):
    idsite = IntegerField(primary_key=True)
    latitude = DecimalField()
    longitude = DecimalField()
    class Meta:
        database = db
        db_table = 'site_locations'

class Earthquake(Model):
    quakeid = IntegerField(primary_key=True)
    magnitude = DecimalField()
    earthquake = CharField()
    date = DateTimeField()

    class Meta:
        database = db
        db_table = 'earthquakes'