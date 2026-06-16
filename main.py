import os
import time
import numpy as np
import onnxruntime as ort
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import serial
import requests
from dotenv import load_dotenv

BAUD_RATE = 115200

load_dotenv()

LOG_FILE = os.getenv("LOG_FILE_PATH")
MODEL_PATH = os.getenv("MODEL_FILE_PATH")
ESP32_URL = os.getenv("ESP32_WEBHOOK_URL")

class NPUClassifier:
    def __init__(self, model_path):
        print(f"Loading {model_path} into ONNX Runtime...")
        self.session = ort.InferenceSession(model_path)
        self.input_name = self.session.get_inputs()[0].name
        print("NPU Inference Engine Active and Waiting.\n")

    def classify(self, text):
        input_data = np.array([[text]], dtype=object)
        outputs = self.session.run(None, {self.input_name: input_data})
        return outputs[0][0]

class LogMonitor(FileSystemEventHandler):
    def __init__(self, classifier, log_file):
        self.classifier = classifier
        self.log_file = log_file
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            self.last_position = f.tell()

    def on_modified(self, event):
        if event.src_path.endswith(self.log_file):
            time.sleep(0.05) 
            try:
                with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(self.last_position)
                    new_lines = f.readlines()
                    self.last_position = f.tell()

                    for line in new_lines:
                        line = line.strip()
                        if line:
                            label = self.classifier.classify(line)
                            self.print_alert(line, label)
            except Exception:
                pass 

    def print_alert(self, log, label):
        if label == "SAFE":
            status = "\033[92m[  SAFE  ]\033[0m"   # Green
        elif label == "WARN":
            status = "\033[93m[  WARN  ]\033[0m"   # Yellow/Orange
        else:
            status = "\033[91m[ THREAT ]\033[0m"   # Red

        print(f"{status} {log}")

        ip_addr = log.split('-')[0].split(']')[-1].strip()
        
        packet = f"SEV:{label}|IP:{ip_addr}\n"
        

        try:
            requests.post(ESP32_URL, data=packet, timeout=1.5)
        except requests.exceptions.RequestException:
            pass

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'a').close()
        
    ai_engine = NPUClassifier(MODEL_PATH)
    event_handler = LogMonitor(ai_engine, LOG_FILE)
    
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()

    print(f"Monitoring {LOG_FILE} for live attacks...")
    print("Press Ctrl+C to stop.\n" + "="*70)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()