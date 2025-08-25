import sys
import os
import ctypes
import subprocess
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

# --- FTP CONFIG ---
USERNAME = "testuser"
PASSWORD = "testpass"
FTP_DIRECTORY = r"C:\Shared"  # Change this to your folder

# Setup authorizer
authorizer = DummyAuthorizer()
authorizer.add_user(USERNAME, PASSWORD, FTP_DIRECTORY, perm="elradfmwMT")

# Setup handler
handler = FTPHandler
handler.authorizer = authorizer
handler.passive_ports = range(60000, 65535)

# Start server
server = FTPServer(("0.0.0.0", 21), handler)

print(f"FTP server running.\n"
      f"Connect using:\n"
      f"  Host: <your IP>\n"
      f"  Port: 21\n"
      f"  User: {USERNAME}\n"
      f"  Pass: {PASSWORD}")

try:
    add_firewall_rules()
    server.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down server...")
finally:
    remove_firewall_rules()
    print("Server closed and firewall rules cleaned up.")
