const int shutterPin = 10;    // Pin connected to transistor base via 1k resistor
const int buttonPin = 2;      // Pin connected to button (using INPUT_PULLUP)
const int numSlides = 40;     // Number of slides to take bracketed shots of. Change as needed
const int bracketCount = 3;   // Number of bracketed exposures per slide. Change as needed

bool lastButtonState = HIGH;
bool buttonPressed = false;

void setup() {
  pinMode(shutterPin, OUTPUT);
  digitalWrite(shutterPin, LOW); // Make sure the shutter line is LOW initially

  pinMode(buttonPin, INPUT_PULLUP); // Internal pull-up so button connects to GND when pressed

  Serial.begin(9600); // For optional debugging
  Serial.println("Ready to take 40 bracketed photos (3 exposures per slide). Press the button to begin.");
}

void loop() {
  // Read button state
  bool currentButtonState = digitalRead(buttonPin);

  // Detect falling edge (button press)
  if (lastButtonState == HIGH && currentButtonState == LOW) {
    buttonPressed = true;
  }

  lastButtonState = currentButtonState;

  // If a button press was detected, run the bracketed sequence
  if (buttonPressed) {
    Serial.println("Button pressed! Taking 40 bracketed photos...");

    for (int i = 0; i < numSlides; i++) {
      Serial.print("Slide ");
      Serial.print(i + 1);
      Serial.println(":");

      for (int j = 0; j < bracketCount; j++) {
        Serial.print("  Exposure ");
        Serial.println(j + 1);

        // Simulate shutter press
        digitalWrite(shutterPin, HIGH);
        delay(100); // Hold shutter press for 100ms
        digitalWrite(shutterPin, LOW);
        delay(0500); // Wait 0.5s between exposures to allow camera to write from the buffer. Change as needed based on camera. Higher end DSLR or mirrorless camera may only need a 0.1s delay and a lower end camera like a D3200 might need 1-1.5 seconds if shooting raw. 
      }
    }

    Serial.println("Done. Waiting for next button press...");
    buttonPressed = false; // Reset flag
  }
}
