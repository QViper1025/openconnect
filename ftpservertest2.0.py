import sys
import os
import ctypes
import subprocess
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer


def run_as_admin():
    """Restart the script with admin rights if not already elevated."""
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    if not is_admin:
        params = " ".join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1
        )
        sys.exit(0)


def add_firewall_rules():
    """Add temporary firewall rules for FTP."""
    print("Adding firewall rules...")
    subprocess.run([
        "netsh", "advfirewall", "firewall", "add", "rule",
        "name=FTP_Server_Port21", "dir=in", "action=allow",
        "protocol=TCP", "localport=21"
    ], check=False)
    subprocess.run([
        "netsh", "advfirewall", "firewall", "add", "rule",
        "name=FTP_Server_Passive", "dir=in", "action=allow",
        "protocol=TCP", "localport=60000-65535"
    ], check=False)


def remove_firewall_rules():
    """Remove firewall rules after server stops."""
    print("Removing firewall rules...")
    subprocess.run([
        "netsh", "advfirewall", "firewall", "delete", "rule",
        "name=FTP_Server_Port21"
    ], check=False)
    subprocess.run([
        "netsh", "advfirewall", "firewall", "delete", "rule",
        "name=FTP_Server_Passive"
    ], check=False)


# Ensure admin rights
run_as_admin()

# --- Shared_FTP Folder Logic ---
def find_shared_ftp_folder():
    for root, dirs, files in os.walk('C:\\'):
        for d in dirs:
            if d == 'Shared_FTP':
                return os.path.join(root, d)
    return None

def prompt_for_shared_folder():
    root = tk.Tk()
    root.withdraw()
    result = messagebox.askyesno('Shared_FTP Not Found', 'No "Shared_FTP" folder found. Would you like to create one?')
    if result:
        choice = simpledialog.askstring('Choose Method', 'Type "text" to enter a path or "browse" to select a directory:')
        if choice and choice.lower() == 'text':
            path = simpledialog.askstring('Enter Path', 'Enter the full directory path where "Shared_FTP" should be created:')
        elif choice and choice.lower() == 'browse':
            path = filedialog.askdirectory(title='Select Directory for Shared_FTP')
        else:
            path = None
        if path:
            shared_ftp_path = os.path.join(path, 'Shared_FTP')
            os.makedirs(shared_ftp_path, exist_ok=True)
            messagebox.showinfo('Folder Created', f'Created: {shared_ftp_path}')
            root.destroy()
            return shared_ftp_path
    # If user says no or cancels, create at C:\Shared_FTP
    shared_ftp_path = r'C:\Shared_FTP'
    os.makedirs(shared_ftp_path, exist_ok=True)
    messagebox.showinfo('Folder Created', f'Created: {shared_ftp_path}')
    root.destroy()
    return shared_ftp_path

shared_ftp_path = find_shared_ftp_folder()
if not shared_ftp_path:
    shared_ftp_path = prompt_for_shared_folder()

# --- FTP CONFIG ---
USERNAME = "testuser"
PASSWORD = "testpass"
FTP_DIRECTORY = shared_ftp_path

# Setup authorizer
authorizer = DummyAuthorizer()
authorizer.add_user(USERNAME, PASSWORD, FTP_DIRECTORY, perm="elradfmwMT")

# Setup handler
handler = FTPHandler
handler.authorizer = authorizer
handler.passive_ports = range(60000, 65535)

# Start server
server = FTPServer(("0.0.0.0", 21), handler)

import socket
local_ip = socket.gethostbyname(socket.gethostname())
print(f"FTP server running.\n"
      f"Connect using:\n"
      f"  Host: {local_ip}\n"
      f"  Port: 21\n"
      f"  User: {USERNAME}\n"
      f"  Pass: {PASSWORD}")

try:
    add_firewall_rules()
    server.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down server...")
finally:
    # Launch trailing cleanup script
    subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), 'ftp_cleanup_trailer.py')])
    # Double-check and force delete rules if still present
    subprocess.run([
        "netsh", "advfirewall", "firewall", "delete", "rule", "name=FTP_Server_Port21"
    ], check=False)
    subprocess.run([
        "netsh", "advfirewall", "firewall", "delete", "rule", "name=FTP_Server_Passive"
    ], check=False)
