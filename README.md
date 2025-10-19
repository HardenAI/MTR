# Synapse MTR - Network Diagnostic Tool

**Version 1.0.0**

![Icon](icon.ico)

A graphical network diagnostic tool for Windows, inspired by the functionality of `mtr`. This application provides a real-time analysis of the network path to a specified host by combining the features of `traceroute` and `ping` into a single, easy-to-use interface.

## Features

- **Integrated Network Path Analysis:** Combines traceroute and continuous ping to provide a comprehensive view of the connection quality to a destination.
- **Real-time Statistics:** Displays live updates for each hop, including packet loss, sent/received packets, latency (best, average, worst, last), and jitter.
- **Connection Stability Analysis:** Automatically assesses the stability of each hop, categorizing it as "Excellent," "Good," "Fair," or "Poor" based on loss and latency metrics.
- **Intuitive UI:** Uses color-coding in the results table (green, amber, red) to provide immediate visual feedback on network health.
- **Host Management:** Allows you to save and quickly select frequently used hostnames or IP addresses.
- **HTML Export:** Export the current network report to a self-contained HTML file for sharing or later analysis.
- **Persistent Configuration:** Remembers the last used window size and position, as well as your saved server list.

## Requirements

- Python 3.x
- PyQt6
- Scapy

All required Python libraries are listed in the `requirements.txt` file.

## Installation

1.  **Clone the repository or download the source files.**

2.  **Create and activate a Python virtual environment:**
    ```bash
    # Create the virtual environment
    python -m venv .venv

    # Activate on Windows
    .venv\Scripts\activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the application:**
    ```bash
    python mtr.py
    ```

2.  **Start a Test:**
    - Enter a hostname (e.g., `google.com`) or an IP address in the **Host** field.
    - Click the **Start** button or press `Enter`.

3.  **Manage Hosts:**
    - To save a new host, type it in the **Host** field and click the **Save** button.
    - Previously saved hosts can be selected from the dropdown menu.

4.  **Export Data:**
    - While a test is running or after it has finished, click the **Export to HTML** button to save the results.

## Configuration

The application stores all its settings in a `conf.json` file, which is created automatically in the application's root directory.

- `servers`: A list of your saved hostnames.
- `geometry`: A hexadecimal string representing the window's last saved size and position.

Deleting this file will reset the application to its default settings.
