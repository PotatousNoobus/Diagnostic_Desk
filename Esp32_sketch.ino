#include <WiFi.h>
#include <WebServer.h>
#include <secrets.h>

const char* ssid = SECRET_WIFI_SSID;
const char* password = SECRET_WIFI_PASS;

WebServer server(80);

const char* dashboard_html = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>NPU Watchdog IDS</title>
    <style>
        body { font-family: 'Courier New', Courier, monospace; background-color: #0a0a0a; color: #00ff00; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: auto; }
        h1 { border-bottom: 2px solid #333; padding-bottom: 10px; color: #fff; }
        .log-box { background: #111; border: 1px solid #333; padding: 15px; border-radius: 5px; height: 400px; overflow-y: auto; }
        .log-entry { margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px dashed #222; }
        .safe { color: #00ff00; }
        .warn { color: #ffaa00; }
        .threat { color: #ff0000; font-weight: bold; }
        .header-bar { display: flex; justify-content: space-between; align-items: center; }
        .status-indicator { padding: 5px 15px; border-radius: 3px; background: #222; border: 1px solid #444; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h1>Intrusion Detection System</h1>
            <div class="status-indicator" id="status">System Active</div>
        </div>
        <p>Live threat interceptions from the Ryzen NPU.</p>
        <div class="log-box" id="logContainer">
            <div style="color: #666;">Waiting for network traffic...</div>
        </div>
    </div>

    <script>
        setInterval(function() {
            fetch('/logs')
            .then(response => response.text())
            .then(data => {
                if(data.trim() !== "") {
                    document.getElementById("logContainer").innerHTML = data;
                }
            });
        }, 2000);
    </script>
</body>
</html>
)rawliteral";

const int MAX_LOGS = 15;
String alertLogs[MAX_LOGS];
int logIndex = 0;

#define GREEN_LED 18
#define ORANGE_LED 5

void setup() {
  Serial.begin(115200);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(ORANGE_LED, OUTPUT);

  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(ORANGE_LED, LOW);

  Serial.print("Connecting to Wi-Fi");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected!");
  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());

  server.on("/", HTTP_GET, []() {
    server.send(200, "text/html", dashboard_html);
  });

  server.on("/logs", HTTP_GET, []() {
    String logHtml = "";
    for (int i = 0; i < MAX_LOGS; i++) {
      int idx = (logIndex - 1 - i + MAX_LOGS) % MAX_LOGS;
      if (alertLogs[idx].length() > 0) {
        logHtml += alertLogs[idx];
      }
    }
    server.send(200, "text/html", logHtml);
  });

  server.on("/update", HTTP_POST, handleUpdate);

  server.begin();
  Serial.println("HTTP Server Started. Waiting for NPU data...");
}

void loop() {
  server.handleClient();
}

void handleUpdate() {
  if (server.hasArg("plain")) {
    String incoming = server.arg("plain");
    
    if (incoming.startsWith("SEV:")) {
      int pipeIndex = incoming.indexOf('|');
      String severity = incoming.substring(4, pipeIndex);
      String ipData = incoming.substring(pipeIndex + 4);
      
      if (severity == "SAFE") {
        digitalWrite(GREEN_LED, HIGH); digitalWrite(ORANGE_LED, LOW);
      } else if (severity == "WARN" || severity == "THREAT") {
        digitalWrite(GREEN_LED, LOW); digitalWrite(ORANGE_LED, HIGH);
      }

      String cssClass = "safe";
      String icon = "✅";
      if (severity == "WARN") { cssClass = "warn"; icon = "⚠️"; }
      if (severity == "THREAT") { cssClass = "threat"; icon = "🚨"; }

      String newLog = "<div class='log-entry " + cssClass + "'>" + 
                      icon + " <strong>[" + severity + "]</strong> " + 
                      "Target: " + ipData + "</div>";

      alertLogs[logIndex] = newLog;
      logIndex = (logIndex + 1) % MAX_LOGS; 
    }
  }
  server.send(200, "text/plain", "Alert Received");
}