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

        @app.route('/assets/<path:filename>')
        def serve_assets(filename):
            return send_from_directory(os.path.join(static_dir, 'assets'), filename)

        # SPA fallback: serve index.html for all non-API routes
        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve_spa(path):
            if path.startswith('api/'):
                return {'error': 'not found'}, 404
            return send_from_directory(static_dir, 'index.html')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=False)
