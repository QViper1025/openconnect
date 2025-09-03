import os
import sys
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def create_shared_folder():
    folder_path = r"C:\Shared"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print("Folder 'Shared' created at C:\\")
    else:
        print("Folder 'Shared' already exists at C:\\")

if __name__ == '__main__':
    if is_admin():
        create_shared_folder()
    else:
        # Re-run the script with admin privileges
        script = sys.argv[0]
        params = " ".join([script] + sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1)
