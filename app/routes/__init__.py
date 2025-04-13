from .auth import auth_bp
from .employees import employees_bp
from .users import users_bp
from .documents import documents_bp
from .clients import clients_bp
from .projects import projects_bp
from .interviews import interviews_bp
from .chats import chats_bp
from .prompt import prompt_bp
from .rag import rag_bp


def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(interviews_bp)
    app.register_blueprint(chats_bp)
    app.register_blueprint(prompt_bp)
    app.register_blueprint(rag_bp)

