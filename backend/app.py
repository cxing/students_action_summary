from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.secret_key = 'change-me-in-production'
    CORS(app, supports_credentials=True, origins=['http://localhost:5173'])

    from auth import auth_bp
    app.register_blueprint(auth_bp)

    from submit import submit_bp
    app.register_blueprint(submit_bp)

    from teacher import teacher_bp
    app.register_blueprint(teacher_bp)

    @app.route('/api/health')
    def health():
        return {'ok': True}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
