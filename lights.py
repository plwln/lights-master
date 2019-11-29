from flask import Flask
from gevent.pywsgi import WSGIServer
from app import app
if __name__ == '__main__':
    # Debug/Development
    app.run(debug=True, host="0.0.0.0", port="5000")
