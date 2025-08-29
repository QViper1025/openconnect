import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ftplib import FTP, error_perm
import subprocess
import platform
import webbrowser

class FTPGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FTP Client")
        self.root.geometry("1200x800")

        self.ftp = None
        self.local_cwd = os.path.expanduser("~")
        self.server_cwd = "/"

        # --- Top Frame: Connection ---
        top_frame = ttk.Frame(root)
        top_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(top_frame, text="Host:").pack(side="left")
        self.host_entry = ttk.Entry(top_frame, width=15)
        self.host_entry.pack(side="left", padx=2)
        ttk.Label(top_frame, text="User:").pack(side="left")
        self.user_entry = ttk.Entry(top_frame, width=12)
        self.user_entry.pack(side="left", padx=2)
        ttk.Label(top_frame, text="Pass:").pack(side="left")
        self.pass_entry = ttk.Entry(top_frame, width=12, show="*")
        self.pass_entry.pack(side="left", padx=2)
        ttk.Label(top_frame, text="Port:").pack(side="left")
        self.port_entry = ttk.Entry(top_frame, width=5)
        self.port_entry.insert(0, "21")
        self.port_entry.pack(side="left", padx=2)

        ttk.Button(top_frame, text="Connect", command=self.connect_ftp).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Browse...", command=self.browse_local_folder).pack(side="left", padx=5)

        # --- Main Frame: Local / Server Panels ---
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Local panel
        local_frame = ttk.Frame(main_frame)
        local_frame.pack(side="left", fill="both", expand=True, padx=5)
        ttk.Label(local_frame, text="Local Files").pack()
        self.local_list = tk.Listbox(local_frame, selectmode=tk.EXTENDED)
        self.local_list.pack(fill="both", expand=True)
        self.local_list.bind("<Double-1>", self.local_double_click)

        local_btn_frame = ttk.Frame(local_frame)
        local_btn_frame.pack(fill="x", pady=2)
        ttk.Button(local_btn_frame, text="Open File", command=self.open_local_file).pack(side="left", padx=2)
        ttk.Button(local_btn_frame, text="Upload →", command=self.upload_selected).pack(side="left", padx=2)

        # Server panel
        server_frame = ttk.Frame(main_frame)
        server_frame.pack(side="right", fill="both", expand=True, padx=5)
        ttk.Label(server_frame, text="Server Files").pack()
        self.server_list = tk.Listbox(server_frame, selectmode=tk.EXTENDED)
        self.server_list.pack(fill="both", expand=True)
        self.server_list.bind("<Double-1>", self.server_double_click)

        server_btn_frame = ttk.Frame(server_frame)
        server_btn_frame.pack(fill="x", pady=2)
        ttk.Button(server_btn_frame, text="← Download", command=self.download_selected).pack(side="left", padx=2)
        ttk.Button(server_btn_frame, text="Delete", command=self.delete_selected).pack(side="left", padx=2)

        # --- Status Box ---
        status_frame = ttk.Frame(root)
        status_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.status_box = tk.Text(status_frame, height=10, wrap="word")
        self.status_box.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(status_frame, command=self.status_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.status_box.config(yscrollcommand=scrollbar.set, state="disabled")
        self.status_box.bind("<Up>", self.scroll_status)
        self.status_box.bind("<Down>", self.scroll_status)

        self.refresh_local_list()

    # --- Status / Log ---
    def log(self, msg):
        self.status_box.config(state="normal")
        self.status_box.insert(tk.END, msg + "\n")
        self.status_box.see(tk.END)
        self.status_box.config(state="disabled")

    def scroll_status(self, event):
        self.status_box.see(tk.END)
        return "break"

    # --- Local Operations ---
    def refresh_local_list(self):
        self.local_list.delete(0, tk.END)
        try:
            self.local_list.insert(tk.END, "..")
            for f in os.listdir(self.local_cwd):
                self.local_list.insert(tk.END, f + ("/" if os.path.isdir(os.path.join(self.local_cwd, f)) else ""))
        except Exception as e:
            self.local_list.insert(tk.END, f"Error: {e}")

    def local_double_click(self, event):
        sel = self.local_list.get(self.local_list.curselection())
        if sel == "..":
            self.local_cwd = os.path.dirname(self.local_cwd)
        else:
            path = os.path.join(self.local_cwd, sel.rstrip("/"))
            if os.path.isdir(path):
                self.local_cwd = path
        self.refresh_local_list()

    def browse_local_folder(self):
        folder = filedialog.askdirectory(initialdir=self.local_cwd)
        if folder:
            self.local_cwd = folder
            self.refresh_local_list()

    def open_local_file(self):
        selections = self.local_list.curselection()
        for idx in selections:
            path = os.path.join(self.local_cwd, self.local_list.get(idx).rstrip("/"))
            if os.path.isfile(path):
                try:
                    if platform.system() == "Windows":
                        os.startfile(path)
                    elif platform.system() == "Darwin":
                        subprocess.call(("open", path))
                    else:
                        subprocess.call(("xdg-open", path))
                    self.log(f"Opened: {path}")
                except Exception as e:
                    self.log(f"Cannot open {path}: {e}")

    # --- FTP Operations ---
    def connect_ftp(self):
        host = self.host_entry.get().strip() or "127.0.0.1"
        user = self.user_entry.get().strip() or "anonymous"
        passwd = self.pass_entry.get().strip()
        try:
            port = int(self.port_entry.get().strip())
        except:
            port = 21
        try:
            self.ftp = FTP()
            self.ftp.connect(host, port, timeout=5)
            self.ftp.login(user, passwd)
            self.server_cwd = self.ftp.pwd()
            self.refresh_server_list()
            self.log(f"Connected to {host}:{port} as {user}")
        except Exception as e:
            self.log(f"FTP connect error: {e}")

    def refresh_server_list(self):
        self.server_list.delete(0, tk.END)
        if not self.ftp:
            return
        try:
            self.server_list.insert(tk.END, "..")
            self.ftp.cwd(self.server_cwd)
            for name in self.ftp.nlst():
                try:
                    self.ftp.cwd(name)
                    self.server_list.insert(tk.END, name + "/")
                    self.ftp.cwd(self.server_cwd)
                except error_perm:
                    self.server_list.insert(tk.END, name)
        except Exception as e:
            self.server_list.insert(tk.END, f"Error: {e}")

    def server_double_click(self, event):
        sel = self.server_list.get(self.server_list.curselection())
        if sel == "..":
            self.ftp.cwd("..")
        else:
            try:
                self.ftp.cwd(sel.rstrip("/"))
            except:
                self.log(f"Selected file: {sel}")
                return
        self.server_cwd = self.ftp.pwd()
        self.refresh_server_list()

    # --- Upload / Download / Delete ---
    def upload_selected(self):
        if not self.ftp:
            self.log("Not connected to FTP")
            return
        selections = self.local_list.curselection()
        for idx in selections:
            fname = self.local_list.get(idx).rstrip("/")
            path = os.path.join(self.local_cwd, fname)
            if os.path.isfile(path):
                try:
                    with open(path, "rb") as f:
                        self.ftp.storbinary(f"STOR {fname}", f)
                    self.log(f"Uploaded: {fname}")
                except Exception as e:
                    self.log(f"Upload error: {fname} {e}")
        self.refresh_server_list()

    def download_selected(self):
        if not self.ftp:
            self.log("Not connected to FTP")
            return
        selections = self.server_list.curselection()
        for idx in selections:
            fname = self.server_list.get(idx).rstrip("/")
            if fname.endswith("/"):
                continue
            try:
                with open(os.path.join(self.local_cwd, fname), "wb") as f:
                    self.ftp.retrbinary(f"RETR {fname}", f.write)
                self.log(f"Downloaded: {fname}")
            except Exception as e:
                self.log(f"Download error: {fname} {e}")
        self.refresh_local_list()

    def delete_selected(self):
        if not self.ftp:
            self.log("Not connected to FTP")
            return
        selections = self.server_list.curselection()
        for idx in selections:
            fname = self.server_list.get(idx).rstrip("/")
            try:
                self.ftp.delete(fname)
                self.log(f"Deleted: {fname}")
            except Exception as e:
                self.log(f"Delete error: {fname} {e}")
        self.refresh_server_list()

if __name__ == "__main__":
    root = tk.Tk()
    app = FTPGuiApp(root)
    root.mainloop()
