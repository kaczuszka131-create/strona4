from flask import Flask, render_template, request, jsonify
import time
import os

app = Flask(__name__)

clients = {}

@app.route("/")
def index():
    return render_template("index.html")

# klient się zgłasza
@app.route("/api/register", methods=["POST"])
def register():

    data = request.json
    cid = data.get("id")

    clients[cid] = {
        "id": cid,
        "ip": request.remote_addr,
        "last_seen": time.time()
    }

    return jsonify({"status": "ok"})


# lista klientów do panelu
@app.route("/api/clients")
def get_clients():

    now = time.time()

    result = []

    for c in clients.values():
        result.append({
            "id": c["id"],
            "ip": c["ip"],
            "last_seen": c["last_seen"]
        })

    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
