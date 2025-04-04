from flask import Flask, redirect
from flasgger import Swagger
from .routes import register_routes

def create_app():
    app = Flask(__name__)

    Swagger(app)

    @app.route('/')
    def redirect_to_docs():
        return redirect('/apidocs')

    register_routes(app)

    return app
