import subprocess
import sys
import ctypes

# UAC/admin rights check
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

# Delete FTP firewall rules
subprocess.run([
    "netsh", "advfirewall", "firewall", "delete", "rule", "name=FTP_Server_Port21"
], check=False)
subprocess.run([
    "netsh", "advfirewall", "firewall", "delete", "rule", "name=FTP_Server_Passive"
], check=False)
print("\nFirewall rules deleted.\nServer closed and firewall rules cleaned up.")
input("\nPress Enter to exit...")
