#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
// Initialize OLED on standard I2C address 0x3C
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// Define LED Pins
#define GREEN_LED 18
#define ORANGE_LED 5

void setup() {
  Serial.begin(115200);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(ORANGE_LED, OUTPUT);

  // Boot Sequence: System starts in SAFE mode
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(ORANGE_LED, LOW);

  Serial.println("System initialized. Running in headless mode (No Display).");

  // if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
  //   Serial.println("OLED allocation failed");
  //   for(;;); // Freeze if screen is missing
  // }
  
  // display.clearDisplay();
  // display.setTextSize(1);
  // display.setTextColor(WHITE);
  // display.setCursor(0, 10);
  // display.println("NPU Watchdog Active");
  // display.println("Listening for traffic...");
  // display.display();
}

void loop() {
  // Check if Python sent a new NPU prediction
  if (Serial.available() > 0) {
    String incoming = Serial.readStringUntil('\n');
    incoming.trim();

    // Parse the packet: "SEV:THREAT|IP:192.168.1.104"
    if (incoming.startsWith("SEV:")) {
      int pipeIndex = incoming.indexOf('|');
      String severity = incoming.substring(4, pipeIndex);
      
      // Print the received data back to the Serial Monitor for debugging
      Serial.print("Received Command: ");
      Serial.println(severity);

      // Change physical LED states
      if (severity == "SAFE") {
        digitalWrite(GREEN_LED, HIGH);
        digitalWrite(ORANGE_LED, LOW);
        
      } else if (severity == "WARN") {
        digitalWrite(GREEN_LED, LOW);
        digitalWrite(ORANGE_LED, HIGH);
        
      } else if (severity == "THREAT") {
        digitalWrite(GREEN_LED, LOW);
        digitalWrite(ORANGE_LED, HIGH);
      }
    }
  }
}

// void loop() {
//   // Check if Python sent a new NPU prediction
//   if (Serial.available() > 0) {
//     String incoming = Serial.readStringUntil('\n');
//     incoming.trim();

//     // Parse the packet: "SEV:THREAT|IP:192.168.1.104"
//     if (incoming.startsWith("SEV:")) {
//       int pipeIndex = incoming.indexOf('|');
//       String severity = incoming.substring(4, pipeIndex);
//       String ipData = incoming.substring(pipeIndex + 4); // Extracts the IP

//       display.clearDisplay();
//       display.setCursor(0, 10);
//       display.setTextSize(2);

//       if (severity == "SAFE") {
//         digitalWrite(GREEN_LED, HIGH);
//         digitalWrite(ORANGE_LED, LOW);
//         display.println("SAFE");
//         display.setTextSize(1);
//         display.print("\nDevice: ");
//         display.println(ipData);
        
//       } else if (severity == "WARN") {
//         digitalWrite(GREEN_LED, LOW);
//         digitalWrite(ORANGE_LED, HIGH);
//         display.println("WARNING");
//         display.setTextSize(1);
//         display.print("\nProbe: ");
//         display.println(ipData);
        
//       } else if (severity == "THREAT") {
//         digitalWrite(GREEN_LED, LOW);
//         digitalWrite(ORANGE_LED, HIGH);
//         display.println("!THREAT!");
//         display.setTextSize(1);
//         display.print("\nAttacker:\n");
//         display.println(ipData);
//       }
      
//       display.display();
//     }
//   }
// }