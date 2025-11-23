#!/usr/bin/env python3
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "Server läuft!"

@app.route('/test')
def test():
    return {"status": "ok"}

if __name__ == '__main__':
    print("Starting test server on port 8080...")
    app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)
