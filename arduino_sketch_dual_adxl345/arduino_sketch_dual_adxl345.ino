#include <Wire.h>

// ADXL345 I2C addresses
#define ADXL345_1 0x53  // SDO connected to GND
#define ADXL345_2 0x1D  // SDO connected to VCC

// ADXL345 registers
#define POWER_CTL 0x2D
#define DATA_FORMAT 0x31
#define DATAX0 0x32

// Data collection parameters
#define COLLECTION_TIME 30000  // 30 seconds in milliseconds
#define SAMPLE_INTERVAL 20     // 20ms between samples = ~1500 samples in 30 seconds

// Data is streamed directly to serial, no buffering needed
int sampleCount = 0;
bool isRecording = false;
unsigned long recordingStartTime = 0;

void setup() {
  Serial.begin(115200);  // Higher baud rate for faster data transfer
  Wire.begin();
  
  // Initialize ADXL345 #1
  initADXL345(ADXL345_1);
  
  // Initialize ADXL345 #2
  initADXL345(ADXL345_2);
  
  Serial.println("=== Data Recorder System Initialized ===");
  Serial.println("ADXL345 #1 (0x53) and #2 (0x1D) initialized");
  Serial.println("");
  Serial.println("System ready. Send any character to start 30-second recording...");
  delay(500);
}

void loop() {
  // Check for serial input to start recording
  if (Serial.available() > 0) {
    Serial.read();  // Read any character to trigger recording
    startRecording();
  }
  
  // If currently recording, collect data
  if (isRecording) {
    if (millis() - recordingStartTime >= COLLECTION_TIME) {
      // Recording time complete
      isRecording = false;
      Serial.println("END_RECORDING");
    } else {
      // Collect data
      collectSample();
      delay(SAMPLE_INTERVAL);
    }
  }
}

void startRecording() {
  sampleCount = 0;
  isRecording = true;
  recordingStartTime = millis();
  Serial.println("START_RECORDING");
  Serial.println("S1_X_g,S1_Y_g,S1_Z_g,S2_X_g,S2_Y_g,S2_Z_g");
}

void collectSample() {
  
  // Read from sensor 1
  int x1, y1, z1;
  readADXL345(ADXL345_1, x1, y1, z1);
  
  // Read from sensor 2
  int x2, y2, z2;
  readADXL345(ADXL345_2, x2, y2, z2);
  
  // Convert to g-forces (scale factor for +/- 16g range)
  float gx1 = x1 * 0.004;
  float gy1 = y1 * 0.004;
  float gz1 = z1 * 0.004;
  float gx2 = x2 * 0.004;
  float gy2 = y2 * 0.004;
  float gz2 = z2 * 0.004;
  
  // Print to serial in CSV format (6 columns for dual sensors)
  Serial.print(gx1, 3); Serial.print(",");
  Serial.print(gy1, 3); Serial.print(",");
  Serial.print(gz1, 3); Serial.print(",");
  Serial.print(gx2, 3); Serial.print(",");
  Serial.print(gy2, 3); Serial.print(",");
  Serial.println(gz2, 3);
  
  sampleCount++;
}

void initADXL345(int address) {
  // Set data format: +/- 16g range, full resolution
  writeRegister(address, DATA_FORMAT, 0x0B);
  // Enable measurement mode
  writeRegister(address, POWER_CTL, 0x08);
}

void readADXL345(int address, int &x, int &y, int &z) {
  Wire.beginTransmission(address);
  Wire.write(DATAX0);
  Wire.endTransmission();
  Wire.requestFrom(address, 6);
  if (Wire.available() >= 6) {
    x = Wire.read() | (Wire.read() << 8);
    y = Wire.read() | (Wire.read() << 8);
    z = Wire.read() | (Wire.read() << 8);
  }
}

void writeRegister(int address, byte reg, byte value) {
  Wire.beginTransmission(address);
  Wire.write(reg);
  Wire.write(value);
  Wire.endTransmission();
}