from .login import auth_bp
from .employees import employees_bp
from .users import users_bp
from .documents import documents_bp
from .chats import chats_bp
from .prompt import prompt_bp
from .rag import rag_bp
from .forgot_password import forgot_password_bp
from app.routes.analytics import analytics_bp

def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(forgot_password_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(chats_bp)
    app.register_blueprint(prompt_bp)
    app.register_blueprint(rag_bp)
    app.register_blueprint(analytics_bp)

