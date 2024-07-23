import psutil
import subprocess
import time
import threading
from pystray import Icon, Menu, MenuItem
from PIL import Image
import os
import sys
import tkinter as tk
from tkinter import ttk

# Global variable to control the monitoring thread
monitoring = True

def log_error(message):
    """Log errors and important events to a log file."""
    with open("svc_log.txt", "a") as file:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{timestamp} - {message}\n")

def is_process_running(process_name):
    """Check if there is any running process that contains the given name."""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if process_name.lower() in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def start_process(executable_path):
    """Start the process using the given executable path."""
    try:
        subprocess.Popen(executable_path, shell=True)
        log_error(f"Started process: {executable_path}")
    except Exception as e:
        log_error(f"Failed to start process {executable_path}: {e}")

def stop_process(process_name):
    """Stop the process with the given name."""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if process_name.lower() in proc.info['name'].lower():
                proc.terminate()  # Terminate the process
                try:
                    proc.wait(timeout=5)  # Wait up to 5 seconds for termination
                    log_error(f"Terminated process: {process_name}")
                except psutil.TimeoutExpired:
                    proc.kill()  # Force kill if termination times out
                    log_error(f"Killed process after timeout: {process_name}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            log_error(f"Error terminating {process_name}: {e}")

def monitor_processes():
    """Monitor and restart processes if they are not running."""
    global monitoring
    process_names = ["get_rcpready.exe", "get_pasteur.exe", "get_cip.exe"]
    executable_paths = {
        "get_rcpready.exe": r"Z:\RecipeManager\Services\get_rcpready.exe",
        "get_pasteur.exe": r"Z:\RecipeManager\Services\get_pasteur.exe",
        "get_cip.exe": r"Z:\RecipeManager\Services\get_cip.exe"
    }

    while monitoring:
        for process_name in process_names:
            if not is_process_running(process_name):
                log_error(f"{process_name} is not running. Starting it...")
                start_process(executable_paths[process_name])
            else:
                log_error(f"{process_name} is running.")
        
        # Wait for 5 minutes before checking again
        time.sleep(300)

def create_image():
    """Load an image from serv.ico for the system tray icon."""
    icon_path = os.path.join(os.path.dirname(sys.argv[0]), 'Z:\RecipeManager\Services\serv.ico')
    return Image.open(icon_path)

def on_quit(icon, item):
    """Quit the application."""
    global monitoring
    monitoring = False
    stop_all_processes()
    log_error("Application quit.")
    icon.stop()
    sys.exit()

def on_start(icon, item):
    """Start monitoring processes."""
    global monitoring
    if not monitoring:
        monitoring = True
        monitor_thread = threading.Thread(target=monitor_processes, daemon=True)
        monitor_thread.start()
        log_error("Process monitoring started.")

def on_stop(icon, item):
    """Stop monitoring processes."""
    global monitoring
    monitoring = False
    stop_all_processes()
    log_error("Process monitoring stopped.")

def stop_all_processes():
    """Stop all monitored processes."""
    process_names = ["get_rcpready.exe", "get_pasteur.exe", "get_cip.exe"]
    for process_name in process_names:
        stop_process(process_name)

def show_status_window():
    """Show a window with the status of the processes and control buttons."""
    def update_status():
        for process_name in process_names:
            if is_process_running(process_name):
                status_labels[process_name].config(text="Running", foreground="green")
            else:
                status_labels[process_name].config(text="Stopped", foreground="red")

    def start_specific_process(process_name):
        executable_path = executable_paths[process_name]
        start_process(executable_path)
        update_status()

    def stop_specific_process(process_name):
        stop_process(process_name)
        update_status()

    status_window = tk.Tk()
    status_window.title("Service Status")

    process_names = ["get_rcpready.exe", "get_pasteur.exe", "get_cip.exe"]
    executable_paths = {
        "get_rcpready.exe": r"Z:\RecipeManager\Services\get_rcpready.exe",
        "get_pasteur.exe": r"Z:\RecipeManager\Services\get_pasteur.exe",
        "get_cip.exe": r"Z:\RecipeManager\Services\get_cip.exe"
    }

    status_labels = {}

    for process_name in process_names:
        frame = ttk.Frame(status_window)
        frame.pack(fill='x', padx=5, pady=2)

        label = ttk.Label(frame, text=process_name)
        label.pack(side='left', padx=5)

        status_label = ttk.Label(frame, text="Checking...", foreground="blue")
        status_label.pack(side='left', padx=5)
        status_labels[process_name] = status_label

        start_button = ttk.Button(frame, text="Start", command=lambda p=process_name: start_specific_process(p))
        start_button.pack(side='left', padx=5)

        stop_button = ttk.Button(frame, text="Stop", command=lambda p=process_name: stop_specific_process(p))
        stop_button.pack(side='left', padx=5)

    update_status()
    status_window.mainloop()

def setup_tray():
    """Setup the system tray icon and menu."""
    icon = Icon("Process Monitor")
    icon.icon = create_image()
    icon.menu = Menu(
        MenuItem("Start", on_start),
        MenuItem("Stop", on_stop),
        MenuItem("Show", lambda icon, item: threading.Thread(target=show_status_window).start()),
        MenuItem("Quit", on_quit)
    )
    icon.run()

if __name__ == "__main__":
    # Start the monitoring thread
    monitor_thread = threading.Thread(target=monitor_processes, daemon=True)
    monitor_thread.start()

    # Setup the system tray icon
    setup_tray()
