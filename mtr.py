import sys
import socket
import time
import math # Using for float('inf')
from collections import defaultdict
import json
import os

# Import necessary PyQt6 libraries and widgets
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QStatusBar, QLabel, QComboBox,
                             QFileDialog, QSizePolicy, QHeaderView, QStackedWidget)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QByteArray
from PyQt6.QtGui import QColor, QIcon, QPixmap

# Suppress Scapy's verbose logging to keep the output clean
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import IP, ICMP, sr1

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class MtrWorker(QThread):
    """
    Handles all network operations (traceroute and ping) in a background thread
    to keep the UI responsive and avoid freezing the application.
    """
    status_update = pyqtSignal(str)
    results_update = pyqtSignal(dict)
    route_discovered = pyqtSignal(list)
    last_ping_update = pyqtSignal(float) # Signal for the last ping time of the final hop

    def __init__(self, target):
        super().__init__()
        self.target_host = target
        self.target_ip = ""
        self.is_running = True
        self.stats = {}
        self.hops = []

    def stop(self):
        """Stops the main loop of the thread gracefully."""
        self.status_update.emit("Stopping...")
        self.is_running = False

    def run(self):
        """
        The main logic for the MTR process, executed in two phases.
        1. Traceroute Phase: Discovers the network path to the target.
        2. Continuous Ping Phase: Pings each hop in the path to gather statistics.
        """
        try:
            # Resolve hostname to IP address. This is the first point of potential failure.
            self.target_ip = socket.gethostbyname(self.target_host)
            self.status_update.emit(f"Tracing route to {self.target_host} [{self.target_ip}]...")
        except socket.gaierror:
            self.status_update.emit(f"Error: Cannot resolve hostname '{self.target_host}'")
            return

        # --- Phase 1: Traceroute to discover hops ---
        for ttl in range(1, 41): # Iterate with increasing TTL to find each hop
            if not self.is_running:
                break
            
            packet = IP(dst=self.target_ip, ttl=ttl) / ICMP()
            # Send the packet and wait for a reply
            reply = sr1(packet, timeout=2, verbose=0)

            if reply is None:
                # No reply received within the timeout
                self.hops.append({'hop': ttl, 'ip': "*", 'hostname': "Request timed out."})
            elif reply.type == 11 and reply.code == 0: # TTL expired
                hop_ip = reply.src
                self.hops.append({'hop': ttl, 'ip': hop_ip, 'hostname': hop_ip})
            elif reply.type == 0: # Destination reached
                hop_ip = reply.src
                self.hops.append({'hop': ttl, 'ip': hop_ip, 'hostname': hop_ip})
                break # Traceroute is complete
            else:
                # Handle other ICMP error types
                self.hops.append({'hop': ttl, 'ip': reply.src, 'hostname': 'ICMP Error'})

            # Update the UI with the discovered route so far
            self.route_discovered.emit(self.hops)

        self.status_update.emit("Traceroute complete. Starting continuous ping...")

        # --- Phase 2: Continuous Ping ---
        # Initialize stats dictionary for each valid hop
        for hop in self.hops:
            if hop['ip'] != "*":
                self.stats[hop['ip']] = {
                    'sent': 0, 'recv': 0, 'loss': 0.0,
                    'last': 0, 'avg': 0, 'best': float('inf'), 'worst': 0,
                    'jitter': 0, 'timings': []
                }
        
        # Main ping loop
        while self.is_running:
            for hop_info in self.hops:
                hop_ip = hop_info['ip']
                if hop_ip == "*":
                    continue

                # Construct and send ICMP packet for the specific hop
                packet = IP(dst=self.target_ip, ttl=hop_info['hop']) / ICMP()
                start_time = time.time()
                reply = sr1(packet, timeout=2, verbose=0)
                end_time = time.time()
                
                self.stats[hop_ip]['sent'] += 1

                if reply:
                    latency = (end_time - start_time) * 1000
                    self.stats[hop_ip]['recv'] += 1
                    self.stats[hop_ip]['last'] = latency
                    self.stats[hop_ip]['best'] = min(self.stats[hop_ip]['best'], latency)
                    self.stats[hop_ip]['worst'] = max(self.stats[hop_ip]['worst'], latency)
                    self.stats[hop_ip]['timings'].append(latency)
                    
                    # Emit last ping time for the final destination
                    if hop_ip == self.target_ip:
                        self.last_ping_update.emit(latency)

                    # Calculate Jitter (variation in latency)
                    n = len(self.stats[hop_ip]['timings'])
                    if n > 1:
                        jitters = [abs(self.stats[hop_ip]['timings'][i] - self.stats[hop_ip]['timings'][i-1]) for i in range(1, n)]
                        self.stats[hop_ip]['jitter'] = sum(jitters) / len(jitters)

                    # Calculate running average
                    self.stats[hop_ip]['avg'] = sum(self.stats[hop_ip]['timings']) / n

                # Calculate packet loss percentage
                loss = (self.stats[hop_ip]['sent'] - self.stats[hop_ip]['recv']) / self.stats[hop_ip]['sent'] * 100
                self.stats[hop_ip]['loss'] = loss
            
            # Send updated statistics to the main UI thread
            self.results_update.emit(self.stats)
            time.sleep(1) # Wait 1 second before the next round of pings

        self.status_update.emit("Stopped.")

class MtrApp(QMainWindow):
    """
    The main application window, handling UI setup, user interactions,
    and communication with the MtrWorker thread.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Synapse - Network Diagnostic Tool")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.worker = None
        self.config_file = "conf.json"
        self.config = {}

        # Set a default size and center the window before loading any settings
        self.resize(800, 800)
        self.center_window()

        # --- UI Setup ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        
        # Input controls (host, buttons)
        controls_layout = QHBoxLayout()
        self.target_combo = QComboBox()
        self.target_combo.setEditable(True)
        self.target_combo.setPlaceholderText("Enter or select a host")
        self.target_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.save_button = QPushButton("Save")
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.export_button = QPushButton("Export to HTML")
        self.stop_button.setEnabled(False)
        
        controls_layout.addWidget(QLabel("Host:"))
        controls_layout.addWidget(self.target_combo)
        controls_layout.addWidget(self.save_button)
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        layout.addLayout(controls_layout)
        layout.addWidget(self.export_button)

        # Stacked widget to switch between background image and results table
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # Background image view
        self.background_label = QLabel()
        self.background_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.background_label.setScaledContents(True)
        if os.path.exists(resource_path("back.png")):
            pixmap = QPixmap(resource_path("back.png"))
            self.background_label.setPixmap(pixmap)
            self.background_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            self.background_label.setText("background image 'back.png' not found")
            self.background_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.background_label)

        # MTR results table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Hop #", "Hostname", "Loss %", "Sent", "Recv",
            "Best", "Avg", "Worst", "Last", "Jitter (ms)", "Stability"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.stacked_widget.addWidget(self.table)
        self.stacked_widget.setCurrentIndex(0)

        # Status bar setup
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.last_ping_label = QLabel("Last Ping: N/A")
        self.status_bar.addPermanentWidget(self.last_ping_label)
        
        # --- Connections ---
        self.start_button.clicked.connect(self.start_test)
        self.stop_button.clicked.connect(self.stop_test)
        self.save_button.clicked.connect(self.save_server)
        self.export_button.clicked.connect(self.export_to_html)
        self.target_combo.lineEdit().returnPressed.connect(self.start_test)

        # Load configuration from file, which may override the default size/position
        self.load_config()

    def center_window(self):
        """Centers the main window on the primary screen."""
        screen = QApplication.primaryScreen().geometry()
        window_geom = self.frameGeometry()
        center_point = screen.center()
        window_geom.moveCenter(center_point)
        self.move(window_geom.topLeft())

    def load_config(self):
        """
        Loads configuration from conf.json. If the file or geometry setting doesn't exist,
        the window retains its default centered position and size.
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                
                servers = self.config.get("servers", [])
                self.target_combo.addItems(servers)
                
                geom_hex = self.config.get("geometry")
                if geom_hex:
                    self.restoreGeometry(QByteArray.fromHex(bytes(geom_hex, 'ascii')))

            except (json.JSONDecodeError, IOError) as e:
                self.status_bar.showMessage(f"Could not load config: {e}", 3000)
        else:
            # Create a default config file if it's missing. Geometry is blank.
            self.config = {"servers": [], "geometry": ""}
            self.save_config()

    def save_config(self):
        """Saves the current configuration (servers and window geometry) to conf.json."""
        try:
            items = [self.target_combo.itemText(i) for i in range(self.target_combo.count())]
            self.config["servers"] = sorted(list(set(items)))
            self.config["geometry"] = self.saveGeometry().toHex().data().decode('ascii')

            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.status_bar.showMessage("Configuration saved.", 3000)
        except IOError as e:
            self.status_bar.showMessage(f"Error saving config: {e}", 5000)

    def save_server(self):
        """Adds a new server to the list and saves the configuration."""
        current_text = self.target_combo.currentText()
        if not current_text:
            self.status_bar.showMessage("Cannot save an empty host.", 3000)
            return

        items = [self.target_combo.itemText(i) for i in range(self.target_combo.count())]
        if current_text not in items:
            self.target_combo.addItem(current_text)
            self.status_bar.showMessage(f"Host '{current_text}' added.", 3000)
            self.save_config()
        else:
            self.status_bar.showMessage(f"Host '{current_text}' is already in the list.", 3000)

    def start_test(self):
        """Initiates the MTR test by creating and starting a worker thread."""
        target = self.target_combo.currentText()
        if not target:
            self.status_bar.showMessage("Please enter or select a target host.", 3000)
            return
            
        if self.worker and self.worker.isRunning():
            return

        self.stacked_widget.setCurrentIndex(1)
        self.table.setRowCount(0)
        self.start_button.setEnabled(False)
        self.target_combo.setEnabled(False)
        self.save_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.last_ping_label.setText("Last Ping: N/A")

        self.worker = MtrWorker(target)
        self.worker.status_update.connect(self.status_bar.showMessage)
        self.worker.route_discovered.connect(self.populate_initial_route)
        self.worker.results_update.connect(self.update_table)
        self.worker.last_ping_update.connect(self.update_last_ping_display)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def stop_test(self):
        """Stops the currently running MTR test."""
        if self.worker:
            self.worker.stop()
        self.stop_button.setEnabled(False)

    def on_worker_finished(self):
        """Cleans up after the worker thread has finished."""
        self.start_button.setEnabled(True)
        self.target_combo.setEnabled(True)
        self.save_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.worker = None
        self.stacked_widget.setCurrentIndex(0)

    def update_last_ping_display(self, latency):
        """Updates the 'Last Ping' label in the status bar."""
        self.last_ping_label.setText(f"Last Ping: {latency:.1f} ms")

    def populate_initial_route(self, hops):
        """Populates the results table with the initial route discovered by the traceroute."""
        self.table.setRowCount(len(hops))
        for row, hop_info in enumerate(hops):
            self.table.setRowHeight(row, 20)
            for col in range(11):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            self.table.item(row, 0).setText(str(hop_info['hop']))
            self.table.item(row, 1).setText(hop_info['hostname'])
            self.table.item(row, 10).setText("Testing...")

    def update_table(self, stats):
        """Updates the results table with new statistics from the worker."""
        for row in range(self.table.rowCount()):
            hostname_item = self.table.item(row, 1)
            if not hostname_item:
                continue
            
            ip_addr = hostname_item.text()
            if ip_addr in stats:
                s = stats[ip_addr]
                loss = s['loss']

                if loss > 10:
                    bg_color = QColor(230, 81, 81)
                    fg_color = QColor("white")
                elif loss > 1:
                    bg_color = QColor(255, 214, 112)
                    fg_color = QColor("black")
                else:
                    bg_color = QColor(165, 214, 167)
                    fg_color = QColor("black")

                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(bg_color)
                        item.setForeground(fg_color)

                self.table.item(row, 2).setText(f"{loss:.1f}")
                self.table.item(row, 3).setText(str(s['sent']))
                self.table.item(row, 4).setText(str(s['recv']))
                best_str = f"{s['best']:.1f}" if s['best'] != float('inf') else "0.0"
                self.table.item(row, 5).setText(best_str)
                self.table.item(row, 6).setText(f"{s['avg']:.1f}")
                self.table.item(row, 7).setText(f"{s['worst']:.1f}")
                self.table.item(row, 8).setText(f"{s['last']:.1f}")
                self.table.item(row, 9).setText(f"{s['jitter']:.1f}")

                jitter = s['jitter']
                avg = s['avg']
                stability = "Testing..."
                if s['sent'] > 10:
                    if loss > 10:
                        stability = "Poor"
                    elif loss > 1:
                        stability = "Fair"
                    else:
                        if jitter < 5 and avg < 100:
                            stability = "Excellent"
                        elif jitter < 15 and avg < 200:
                            stability = "Good"
                        else:
                            stability = "Fair"
                self.table.item(row, 10).setText(stability)

    def export_to_html(self):
        """Exports the current MTR results to an HTML file."""
        target_host = self.target_combo.currentText()
        if self.table.rowCount() == 0:
            self.status_bar.showMessage("No data to export.", 3000)
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Save HTML Report", f"mtr_report_{target_host}.html", "HTML Files (*.html)")
        if not filename:
            return

        try:
            with open(filename, 'w') as f:
                f.write("<html><head><title>MTR Report for " + target_host + "</title>")
                f.write("""
                <style>
                    body { font-family: sans-serif; }
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #dddddd; text-align: left; padding: 8px; }
                    th { background-color: #f2f2f2; }
                </style>
                """)
                f.write("</head><body>")
                f.write(f"<h1>MTR Report for {target_host}</h1>")
                f.write(f"<p>Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>")
                
                f.write("<table><tr>")
                for col in range(self.table.columnCount()):
                    f.write(f"<th>{self.table.horizontalHeaderItem(col).text()}</th>")
                f.write("</tr>")

                for row in range(self.table.rowCount()):
                    bg_color = self.table.item(row, 0).background().color().name()
                    fg_color = self.table.item(row, 0).foreground().color().name()
                    f.write(f"<tr style='background-color:{bg_color}; color:{fg_color};'>")
                    for col in range(self.table.columnCount()):
                        item_text = self.table.item(row, col).text() if self.table.item(row, col) else ""
                        f.write(f"<td>{item_text}</td>")
                    f.write("</tr>")

                f.write("</table></body></html>")
            self.status_bar.showMessage(f"Report saved to {filename}", 5000)
        except IOError:
            self.status_bar.showMessage("Error saving HTML report.", 5000)

    def closeEvent(self, event):
        """
        Handles the window close event. Saves the window geometry and ensures
        the worker thread is stopped cleanly.
        """
        # --- Bug Fix: Only save geometry on close, not the server list ---
        try:
            # Update the geometry in the existing config object
            self.config["geometry"] = self.saveGeometry().toHex().data().decode('ascii')
            # Write the updated config back to the file
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            self.status_bar.showMessage(f"Error saving config: {e}", 5000)

        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MtrApp()
    window.show()
    sys.exit(app.exec())