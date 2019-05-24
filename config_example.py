import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
	HOST = 'YOUR HOSTNAME'
	DATABASE = 'YOUR DATABASE'
	USERNAME = 'YOUR USERNAME'
	SECRET_KEY = 'YOUR PASSWORD'
	PORT = '5432' #default postgresql port number, can change if different
	SSL_DISABLE = False

@staticmethod
def init_app(app):
	pass

@classmethod
def init_app(app):
	Config.init_app(app)

config = {

}