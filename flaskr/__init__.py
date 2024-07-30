import os
from flask import Flask, g, redirect, url_for, session, request
from .auth import auth
from .main import main
from .portfolio import portfolio
from .artwork import artwork
from .pdf import pdf
from dotenv import load_dotenv
from flaskr.db import get_db_connection as connection


def create_app():
    app = Flask(__name__)
    load_dotenv()
    app.secret_key = os.getenv('SESSION_KEY')

    API_URL = os.getenv('API_URL')

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(portfolio)
    app.register_blueprint(artwork, url_prefix='/artwork')
    app.register_blueprint(pdf, url_prefix='/pdf')

    app.config['UPLOAD_FOLDER'] = os.path.join(
        os.getcwd(), 'flaskr/static/uploads')

    @app.before_request
    def before_request():
        g.db = connection()

        if request.endpoint and request.endpoint.startswith('static'):
            return
        if 'user_id' not in session and request.endpoint not in ['auth.login', 'auth.signup', 'portfolio.search_portfolios', 'pdf.download']:
            return redirect(url_for('auth.login'))

    @app.teardown_request
    def after_request(exception):
        db = getattr(g, 'db', None)
        if db is not None:
            db.close()

    return app
