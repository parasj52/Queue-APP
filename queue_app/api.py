# Make imports work whether this file is executed as a script or as a package module.
from controllers import register_routes
from services import initialize

from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize DB / services
initialize()

# Register routes from controller
register_routes(app)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
