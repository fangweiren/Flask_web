import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
	WTF_CSRF_ENABLED = False
	SQLALCHEMY_COMMIT_ON_TEARDOWN = True
	SQLALCHEMY_TRACK_MODIFICATIONS = True
	FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
	FLASKY_MAIL_SENDER = 'Flasky Admin <fangweiren843@163.com>'
	#FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
	FLASKY_ADMIN = 'fangweiren843@163.com'
	FLASKY_POSTS_PER_PAGE = 20

	@staticmethod
	def init_app(app):
		pass

class DevelopmentConfig(Config):
	DEBUG = True
	MAIL_SERVER = 'smtp.163.com'
	MAIL_PORT = 465
	MAIL_USE_SSL = True
	#MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	#MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	MAIL_USERNAME = 'fangweiren843@163.com'
	MAIL_PASSWORD = 'fwr5079843'
	SQLALCHEMY_DATABASE_URI = "mysql://root:123456@localhost/myblog"

class TestingConfig(Config):
	TESTING = True
	SQLALCHEMY_DATABASE_URI = 'mysql://root:123456@localhost/myblog'

class ProductionConfig(Config):
	SQLALCHEMY_DATABASE_URI = 'mysql://root:123456@localhost/myblog'
	
config = {
	'development' : DevelopmentConfig,
	'testing' : TestingConfig,
	'production' : ProductionConfig,
	'default' : DevelopmentConfig
}
