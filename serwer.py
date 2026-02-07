from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import time
import threading

app = Flask(__name__)
CORS(app)

# Przechowywanie klientów
clients = {}
client_lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/clients')
def get_clients():
    """Zwraca listę aktywnych klientów"""
    with client_lock:
        # Czyszczenie nieaktywnych klientów (> 30 sekund)
        current_time = time.time()
        inactive_clients = []
        
        for client_id, client_data in clients.items():
            if current_time - client_data['last_seen'] > 30:
                inactive_clients.append(client_id)
        
        for client_id in inactive_clients:
            del clients[client_id]
        
        # Przygotowanie listy klientów
        client_list = []
        for client_id, client_data in clients.items():
            is_active = current_time - client_data['last_seen'] < 10
            client_list.append({
                'id': client_id,
                'name': client_data.get('name', 'Klient'),
                'status': 'active' if is_active else 'inactive',
                'ip': client_data.get('ip', '0.0.0.0')
            })
        
        return jsonify(client_list)

@app.route('/api/register', methods=['POST'])
def register_client():
    """Rejestracja nowego klienta"""
    try:
        data = request.json
        client_id = data.get('id')
        client_name = data.get('name', 'Klient')
        
        with client_lock:
            clients[client_id] = {
                'name': client_name,
                'last_seen': time.time(),
                'command': None,
                'command_time': None,
                'ip': request.remote_addr
            }
        
        print(f"✅ Zarejestrowano klienta: {client_id}")
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Błąd rejestracji: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_command', methods=['POST'])
def get_command():
    """Klient pobiera swoją komendę"""
    try:
        data = request.json
        client_id = data.get('id')
        
        with client_lock:
            if client_id in clients:
                # Aktualizuj czas ostatniej aktywności
                clients[client_id]['last_seen'] = time.time()
                
                # Sprawdź czy jest komenda
                command = clients[client_id].get('command')
                if command:
                    # Wyczyść komendę po pobraniu
                    clients[client_id]['command'] = None
                    return jsonify({'command': command})
        
        return jsonify({'command': None})
    except Exception as e:
        print(f"❌ Błąd pobierania komendy: {e}")
        return jsonify({'command': None})

@app.route('/api/send_command', methods=['POST'])
def send_command():
    """Wysłanie komendy do klienta"""
    try:
        data = request.json
        client_id = data.get('client_id')
        command = data.get('command')
        
        with client_lock:
            if client_id in clients:
                clients[client_id]['command'] = command
                clients[client_id]['command_time'] = time.time()
                print(f"📤 Wysłano komendę '{command}' do klienta {client_id}")
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Client not found'})
    except Exception as e:
        print(f"❌ Błąd wysyłania komendy: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ping')
def ping():
    """Sprawdzenie statusu serwera"""
    return jsonify({'status': 'online', 'clients_count': len(clients)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)