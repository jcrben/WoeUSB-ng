#!/usr/bin/env python3
from tkinter import ttk, filedialog, messagebox, font, simpledialog
import tkinter as tk
import subprocess
import threading
import queue
import os
import shutil

# Assuming list_devices is in the same directory or accessible
try:
    from . import list_devices
except ImportError:
    import list_devices

class WoeUSBtkinter(tk.Tk):
    def __init__(self):
        super().__init__()
        print("initializing")
        self.title("WoeUSB-ng (Tkinter)")
        
        # DPI/font scaling from env (fallbacks if unset)
        try:
            scale = float(os.environ.get("WOEUSB_TK_SCALE", "2.0"))
        except ValueError:
            scale = 2.0
        self.tk.call('tk', 'scaling', scale)
        self._scale = scale

        # Window size roughly scaled with DPI
        base_w, base_h = 700, 550
        self.geometry(f"{int(base_w*scale)}x{int(base_h*scale)}")

        # Adjust core Tk named fonts so ttk widgets also pick them up
        try:
            default_size = int(os.environ.get("WOEUSB_TK_FONT_SIZE", "14"))
        except ValueError:
            default_size = 14
        for fname in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkTooltipFont"):
            try:
                f = font.nametofont(fname)
                f.configure(size=default_size)
            except Exception:
                pass
        try:
            ffix = font.nametofont("TkFixedFont")
            ffix.configure(size=max(12, default_size - 1))
        except Exception:
            pass

        # Ensure ttk uses default named font unless overridden
        self.style = ttk.Style(self)
        try:
            self.style.configure('.', font=font.nametofont('TkDefaultFont'))
            self.style.configure('TLabelframe.Label', font=font.nametofont('TkDefaultFont'))
            self.style.configure('TCombobox', font=font.nametofont('TkDefaultFont'))
            self.style.configure('TButton', font=font.nametofont('TkDefaultFont'))
            self.style.configure('TLabel', font=font.nametofont('TkDefaultFont'))
            self.style.configure('TEntry', font=font.nametofont('TkDefaultFont'))
        except Exception:
            pass

        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')

        # Header font we fully control (independent of ttk styles)
        try:
            header_px = int(os.environ.get('WOEUSB_HEADER_SIZE', '28'))
        except ValueError:
            header_px = 28
        base_family = font.nametofont('TkDefaultFont').cget('family')
        # Negative size = pixel size (more predictable on some setups)
        self.header_font = font.Font(family=base_family, size=-header_px, weight='bold')

        self.iso_path = tk.StringVar()
        self.target_device = tk.StringVar()
        self.devices = []

        self._create_widgets()
        self._bind_zoom_keys()
        self.refresh_devices()

    def increase_font(self):
        '''Make the font 2 points bigger'''
        print('making font bigger')
        size = self.customFont['size']
        self.customFont.configure(size=size+2)

    def decrease_font(self):
        '''Make the font 2 points smaller'''
        size = self.customFont['size']
        self.customFont.configure(size=size-2)

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create buttonframe as a child of main_frame
        buttonframe = tk.Frame(main_frame)
        self.customFont = tk.font.Font(family="Helvetica", size=50)
        label = tk.Label(main_frame, text="Hello, world", font=self.customFont)
        text = tk.Text(main_frame, width=20, height=2, font=self.customFont)

        buttonframe.pack(side="top", fill="x")
        label.pack(side="top", fill="x")
        text.pack(side="top", fill="both", expand=True)
        text.insert("end","press +/- buttons to change\nfont size")

        increase_font = tk.Button(buttonframe, text="+", command=self.increase_font)
        decrease_font = tk.Button(buttonframe, text="-", command=self.decrease_font)

        increase_font.pack(side="left")
        decrease_font.pack(side="left")



        # --- Source ISO ---
        tk.Label(main_frame, text="Source ISO", font=self.header_font, anchor='w').pack(anchor='w', padx=4)
        source_container = ttk.Frame(main_frame, borderwidth=1, relief="sunken", padding="10")
        source_container.pack(fill=tk.X, pady=(2, 8))

        iso_entry = ttk.Entry(source_container, textvariable=self.iso_path, width=60)
        iso_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), pady=(10,0))

        browse_button = ttk.Button(source_container, text="Browse...", command=self.browse_iso)
        browse_button.pack(side=tk.LEFT, pady=(10,0))

        # --- Target Device ---
        tk.Label(main_frame, text="Target Device", font=self.header_font, anchor='w').pack(anchor='w', padx=4)
        target_container = ttk.Frame(main_frame, borderwidth=1, relief="sunken", padding="10")
        target_container.pack(fill=tk.X, pady=(2, 8))

        self.device_combobox = ttk.Combobox(target_container, textvariable=self.target_device, state="readonly", width=57)
        self.device_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), pady=(10,0))

        refresh_button = ttk.Button(target_container, text="Refresh", command=self.refresh_devices)
        refresh_button.pack(side=tk.LEFT, pady=(10,0))

        # --- Install Button ---
        self.install_button = ttk.Button(main_frame, text="Install", command=self.start_install)
        self.install_button.pack(pady=10, fill=tk.X)

        # --- Progress Bar ---
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)

        # --- Log ---
        tk.Label(main_frame, text="Log", font=self.header_font, anchor='w').pack(anchor='w', padx=4)
        log_container = ttk.Frame(main_frame, borderwidth=1, relief="sunken", padding="10")
        log_container.pack(fill=tk.BOTH, expand=True, pady=(2, 8))

        self.log_text = tk.Text(log_container, state='disabled', wrap='word', height=10, font=font.nametofont('TkFixedFont'))
        scrollbar = ttk.Scrollbar(log_container, command=self.log_text.yview)
        self.log_text['yscrollcommand'] = scrollbar.set
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(10,0))

    def increase_zoom(self):
        print('hmm')
        self._adjust_zoom(0.2)
        
    def _bind_zoom_keys(self):
        print('zooming')
        # Ctrl+'+' zoom in, Ctrl+'-' zoom out, Ctrl+'0' reset
        self.bind_all('<Control-plus>', lambda e: self.increase_zoom())
        self.bind_all('<Control-KP_Add>', lambda e: self._adjust_zoom(0.2))
        self.bind_all('<Control-minus>', lambda e: self._adjust_zoom(-0.2))
        self.bind_all('<Control-KP_Subtract>', lambda e: self._adjust_zoom(-0.2))
        self.bind_all('<Control-0>', lambda e: self._set_zoom(2.0))

    def _set_zoom(self, new_scale: float):
        self._scale = max(0.6, min(new_scale, 5.0))
        self.tk.call('tk', 'scaling', self._scale)
        # Recompute header font in pixels proportional to scale
        try:
            base_family = font.nametofont('TkDefaultFont').cget('family')
            px = int(14 * self._scale * 1.6)  # rough heuristic
            self.header_font.configure(family=base_family, size=-px, weight='bold')
        except Exception:
            pass

    def _adjust_zoom(self, delta: float):
        self._set_zoom(self._scale + delta)

    def browse_iso(self):
        path = filedialog.askopenfilename(
            title="Select an ISO file",
            filetypes=(("ISO files", "*.iso"), ("All files", "*.*"))
        )
        if path:
            self.iso_path.set(path)

    def refresh_devices(self):
        try:
            self.devices = list_devices.get_device_list()
            device_names = [f"{d['name']} - {d['model']} ({d['size']})" for d in self.devices]
            self.device_combobox['values'] = device_names
            if device_names:
                self.device_combobox.current(0)
        except Exception as e:
            self.log(f"Error refreshing devices: {e}")
            messagebox.showerror("Device Error", f"Could not list devices. Make sure 'lsblk' and 'udisksctl' are installed.\nError: {e}")

    def log(self, message):
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.configure(state='disabled')
        self.log_text.see(tk.END)

    def start_install(self):
        iso = self.iso_path.get()
        device_selection = self.target_device.get()

        if not iso or not os.path.exists(iso):
            messagebox.showerror("Error", "Please select a valid ISO file.")
            return

        if not device_selection:
            messagebox.showerror("Error", "Please select a target device.")
            return
        
        # Find the device path from the selection string
        selected_device_path = None
        for device in self.devices:
            if device_selection.startswith(device['name']):
                selected_device_path = f"/dev/{device['name']}"
                break
        
        if not selected_device_path:
            messagebox.showerror("Error", "Could not determine the selected device path.")
            return

        if not messagebox.askokcancel("Confirm", f"This will ERASE all data on {selected_device_path}.\nAre you sure you want to proceed?"):
            return

        self.install_button.config(state="disabled")
        self.progress['value'] = 0
        self.log("Starting installation...")

        self.queue = queue.Queue()
        self.thread = threading.Thread(
            target=self.run_woeusb_process,
            args=(iso, selected_device_path)
        )
        self.thread.start()
        self.after(100, self.process_queue)

    def run_woeusb_process(self, iso, device):
        # Helper to run a command and stream output to the GUI
        def _run_and_stream(cmd, stdin_text=None):
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    stdin=subprocess.PIPE if stdin_text is not None else None,
                )
                if stdin_text is not None and process.stdin:
                    try:
                        process.stdin.write(stdin_text + "\n")
                        process.stdin.flush()
                    except Exception:
                        pass
                    try:
                        process.stdin.close()
                    except Exception:
                        pass
                for line in iter(process.stdout.readline, ''):
                    self.queue.put(line)
                process.stdout.close()
                process.wait()
                return process.returncode
            except FileNotFoundError:
                return 127
            except Exception as e:
                self.queue.put(f"ERROR: Subprocess error: {e}")
                return 1

        # 1) If already root, run directly
        if os.geteuid() == 0:
            rc = _run_and_stream(['woeusb', '--device', iso, device])
        else:
            rc = None
            # 2) Try pkexec if available
            if shutil.which('pkexec'):
                rc = _run_and_stream(['pkexec', 'woeusb', '--device', iso, device])
                if rc != 0:
                    self.queue.put("INFO: pkexec failed or was canceled; trying sudo...")
            else:
                self.queue.put("INFO: pkexec not found; trying sudo...")

            # 3) Fallback to sudo -S (prompt user for password)
            if rc is None or rc != 0:
                pw = None
                try:
                    pw = simpledialog.askstring(
                        "Authentication Required",
                        "Enter your password to run woeusb with sudo:",
                        show='*', parent=self
                    )
                except Exception:
                    pass
                if not pw:
                    self.queue.put("ERROR: Authentication canceled.")
                    return
                rc = _run_and_stream(['sudo', '-S', '-p', '', 'woeusb', '--device', iso, device], stdin_text=pw)

        if rc == 0:
            self.queue.put("INFO: Installation succeeded!")
        else:
            self.queue.put(f"ERROR: Installation failed with return code {rc}.")

    def process_queue(self):
        try:
            while True:
                line = self.queue.get_nowait()
                self.log(line.strip())
                # Simple progress parsing
                if "Erasing" in line:
                    self.progress['value'] = 10
                elif "Partitioning" in line:
                    self.progress['value'] = 25
                elif "Copying" in line:
                    self.progress['value'] = 50
                elif "Installing bootloader" in line:
                    self.progress['value'] = 85
                elif "Installation succeeded" in line:
                    self.progress['value'] = 100
                    self.install_button.config(state="normal")
                    messagebox.showinfo("Success", "The USB drive has been successfully created!")
                elif "ERROR:" in line:
                    self.progress['value'] = 0
                    self.install_button.config(state="normal")
                    messagebox.showerror("Failed", f"Installation failed. Check the log for details.")

        except queue.Empty:
            if self.thread.is_alive():
                self.after(100, self.process_queue)
            else: # Thread finished
                self.install_button.config(state="normal")


def main():
    """Main function to run the Tkinter GUI."""
    # Run the GUI unprivileged; elevation is handled per-operation via pkexec.
    app = WoeUSBtkinter()
    app.mainloop()


if __name__ == "__main__":
    main()
