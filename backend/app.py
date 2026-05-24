from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.secret_key = 'change-me-in-production'
    CORS(app, supports_credentials=True, origins=['http://localhost:5173'])

    @app.route('/api/health')
    def health():
        return {'ok': True}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
