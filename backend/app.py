from flask import Flask, send_from_directory
from flask_cors import CORS
import os


def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')
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

    # Serve frontend in production (static files from build output)
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    if os.path.isdir(static_dir):

        @app.route('/')
        def serve_index():
            return send_from_directory(static_dir, 'index.html')

        @app.route('/assets/<path:filename>')
        def serve_assets(filename):
            return send_from_directory(os.path.join(static_dir, 'assets'), filename)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)
