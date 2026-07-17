from flask import Flask, jsonify
import os
import socket

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({
        "message": "Hello from the GitOps pipeline!",
        "hostname": socket.gethostname(),
        "version": os.environ.get("APP_VERSION", "v1"),
    })


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200


@app.route("/readyz")
def readyz():
    return jsonify({"status": "ready"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
