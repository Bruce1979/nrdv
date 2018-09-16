import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.flask.env'))

class Config(object):
  SECRET_KEY = os.environ.get('SECRET_KEY')
  SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  MAIL_SERVER = os.environ.get('MAIL_SERVER')
  MAIL_PORT = int(os.environ.get('MAIL_PORT'))
  MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
  MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
  MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
  ADMINS = os.environ.get('ADMINS')
  LANGUAGES = os.environ.get('LANGUAGES')
  MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
  ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
  POSTS_PER_PAGE = int(os.environ.get('POSTS_PER_PAGE'))

class TestConfig(Config):
  TESTING = True
  SQLALCHEMY_DATABASE_URI = 'sqlite://'
