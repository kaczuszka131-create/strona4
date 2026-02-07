import socket
import time
import threading
import sys

HOST = "file:///C:/Users/Kamil/Documents/s/serwer/index.html"  # Twój serwer na Render
PORT = 6127

# Tutaj umieść swoje funkcje:
# start(), stop(), epstine.start_epstine_start_in_background(), itp.
# Pamiętaj o importach potrzebnych modułów

def handle_server_commands(server_socket):
    """Obsługa komend z serwera"""
    while True:
        try:
            data = server_socket.recv(1024).decode()
            if not data:
                print("Serwer zakończył połączenie.")
                break

            print(f"Otrzymano komendę: {data}")

            # Tutaj dodaj obsługę swoich komend
            # Przykład:
            if data == "start":
                print("Wykonuję: start")
                # start()
            elif data == "stop":
                print("Wykonuję: stop")
                # stop()
            elif data == "epstine":
                print("Wykonuję: epstine")
                # epstine.start_epstine_start_in_background()
            elif data == "stopepstine":
                print("Wykonuję: stopepstine")
                # epstine.epstinestop()
            elif data == "hideallwindows":
                print("Wykonuję: hideallwindows")
                # hide_all_windows()
            elif data == "call elon musk":
                print("Wykonuję: call elon musk")
                # epstinecall.epstinecall("Elon Musk", tapeta13)
            elif data == "call donald trump":
                print("Wykonuję: call donald trump")
                # epstinecall.epstinecall("Donald Trump", tapeta12)
            elif data == "call epstine":
                print("Wykonuję: call epstine")
                # epstinecall.epstinecall("Jeffrey Epstein", Epstine_img)
            elif data == "powiadomienie epstine":
                print("Wykonuję: powiadomienie epstine")
                # powiadomienia.show_custom_notification(...)
            elif data == "powiadomienie test":
                print("Wykonuję: powiadomienie test")
                # system_notification(...)
            else:
                print(f"Nieznana komenda: {data}")

        except ConnectionResetError:
            print("Połączenie zostało zerwane.")
            break
        except Exception as e:
            print(f"Błąd odbierania komendy: {e}")
            break

def main():
    # Pobierz nazwę programu (możesz zmienić)
    if len(sys.argv) > 1:
        final_name = sys.argv[1]
    else:
        final_name = f"Klient-{socket.gethostname()}"

    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                print(f"Łączenie z serwerem {HOST}:{PORT}...")
                s.connect((HOST, PORT))
                print("Połączono z serwerem.")
                
                # Wysyłanie nazwy programu do serwera
                try:
                    nazwa_programu = f"NAZWA:{final_name}"
                    s.sendall(nazwa_programu.encode())
                    print(f"Wysłano nazwę programu do serwera: {final_name}")
                except Exception as e:
                    print(f"Błąd podczas wysyłania nazwy programu: {e}")
                    continue

                # Uruchomienie wątku do obsługi komend
                command_thread = threading.Thread(target=handle_server_commands, args=(s,))
                command_thread.daemon = True
                command_thread.start()

                # Główna pętla - utrzymanie połączenia
                while True:
                    try:
                        # Wysyłanie pinga co 30 sekund
                        time.sleep(30)
                        s.sendall(b"PING")
                    except (ConnectionResetError, BrokenPipeError):
                        print("Utracono połączenie z serwerem.")
                        break
                    except Exception as e:
                        print(f"Błąd w głównej pętli: {e}")
                        break

        except ConnectionRefusedError:
            print("Serwer niedostępny. Ponowne próbę za 10 sekund...")
        except Exception as e:
            print(f"Błąd połączenia: {e}")
        
        time.sleep(10)

if __name__ == "__main__":
    main()