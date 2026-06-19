import os
import time
import requests
import threading
import csv
import numpy as np
import onnxruntime as ort
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

load_dotenv()

LOG_FILE = os.getenv("LOG_FILE_PATH", "system_errors.log")
MODEL_PATH = os.getenv("MODEL_FILE_PATH", "custom_model.onnx")
ESP32_URL = os.getenv("ESP32_WEBHOOK_URL")

DATASET_FILE = "dataset.csv" 
RETRAIN_THRESHOLD = 5 

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
        
    def reload_model(self, new_model_path):
        print(f"\n\033[96m[HOT-SWAP] Loading newly trained model: {new_model_path}...\033[0m")
        self.session = ort.InferenceSession(new_model_path)
        self.input_name = self.session.get_inputs()[0].name
        print("\033[96m[HOT-SWAP] NPU successfully upgraded. Zero downtime achieved!\033[0m\n")

class LogMonitor(FileSystemEventHandler):
    def __init__(self, classifier, log_file):
        self.classifier = classifier
        self.log_file = log_file
        self.new_threats_count = 0
        self.thread_lock = threading.Lock() 
        
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
            status = "\033[92m[  SAFE  ]\033[0m"
        elif label == "WARN":
            status = "\033[93m[  WARN  ]\033[0m"
        else:
            status = "\033[91m[ THREAT ]\033[0m"

        print(f"{status} {log}")
        
        ip_addr = log.split('-')[0].split(']')[-1].strip()
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        packet = f"SEV:{label}|IP:{ip_addr}|TIME:{current_time}"
        
        try:
            requests.post(ESP32_URL, data=packet, timeout=1.5)
        except:
            pass
            
        if label == "THREAT":
            self.append_to_dataset(log, label)

    def append_to_dataset(self, log, label):
        try:
            with open(DATASET_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([log, label])
            
            with self.thread_lock:
                self.new_threats_count += 1
                print(f"   -> Added to dataset. ({self.new_threats_count}/{RETRAIN_THRESHOLD} until retraining)")
                
                if self.new_threats_count >= RETRAIN_THRESHOLD:
                    self.new_threats_count = 0 
                    self.trigger_brain_2()
        except Exception as e:
            print(f"Error saving to dataset: {e}")

    def trigger_brain_2(self):
        print("\n\033[95m[BRAIN 2 WAKING UP] Threshold reached. Spinning up background thread...\033[0m")
        trainer_thread = threading.Thread(target=self.shadow_trainer_task)
        trainer_thread.start()

    def shadow_trainer_task(self):
        try:
            import pandas as pd
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            from sklearn.pipeline import Pipeline
            from skl2onnx import convert_sklearn
            from skl2onnx.common.data_types import StringTensorType

            print("\033[95m[BRAIN 2] Reading updated dataset.csv...\033[0m")
            df = pd.read_csv(DATASET_FILE, header=None, names=['log', 'label'])
            df = df.dropna()
            
            X = df['log'].values
            y = df['label'].values

            print("\033[95m[BRAIN 2] Vectorizing TF-IDF and training new weights...\033[0m")
            pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=1000)),
                ('clf', LogisticRegression(max_iter=1000, class_weight='balanced'))
            ])
            pipeline.fit(X, y)

            print("\033[95m[BRAIN 2] Exporting to ONNX format...\033[0m")
            initial_type = [('string_input', StringTensorType([None, 1]))]
            onnx_model = convert_sklearn(pipeline, initial_types=initial_type)

            new_model_name = "custom_model_v2.onnx"
            with open(new_model_name, "wb") as f:
                f.write(onnx_model.SerializeToString())

            print(f"\033[95m[BRAIN 2] {new_model_name} successfully generated!\033[0m")
            
            self.classifier.reload_model(new_model_name)

        except Exception as e:
            print(f"\033[91m[BRAIN 2 ERROR] Retraining failed: {e}\033[0m")

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