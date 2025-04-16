const int shutterPin = 10;    // Pin connected to transistor base via 1k resistor
const int buttonPin = 2;      // Pin connected to button (using INPUT_PULLUP)
const int numShots = 40;      // Number of photos to take per press. Change as needed

bool lastButtonState = HIGH;
bool buttonPressed = false;

void setup() {
  pinMode(shutterPin, OUTPUT);
  digitalWrite(shutterPin, LOW); // Make sure the shutter line is LOW initially

  pinMode(buttonPin, INPUT_PULLUP); // Internal pull-up so button connects to GND when pressed

  Serial.begin(9600); // For optional debugging
  Serial.println("Ready to take pictures. Press the button to begin.");
}

void loop() {
  // Read button state
  bool currentButtonState = digitalRead(buttonPin);

  // Detect falling edge (button press)
  if (lastButtonState == HIGH && currentButtonState == LOW) {
    buttonPressed = true;
  }

  lastButtonState = currentButtonState;

  // If a button press was detected, run the photo sequence
  if (buttonPressed) {
    Serial.println("Button pressed! Taking 40 photos...");

    for (int i = 0; i < numShots; i++) {
      Serial.print("Taking photo ");
      Serial.println(i + 1);

      // Simulate shutter press
      digitalWrite(shutterPin, HIGH);
      delay(100); // Hold shutter press for 100ms
      digitalWrite(shutterPin, LOW);
      delay(1000); // Wait 1 second before next shot
    }

    Serial.println("Done. Waiting for next button press...");
    buttonPressed = false; // Reset flag
  }
}
