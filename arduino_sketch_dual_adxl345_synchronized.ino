/*
  ==================================================================================
  SYNCHRONIZED DUAL ADXL345 SENSOR SKETCH FOR ARDUINO UNO
  ==================================================================================
  
  Purpose: Collect data from two ADXL345 accelerometers with SYNCHRONIZED sampling
           to prevent "Multi-Channel Synchronization Issue" errors
  
  Hardware Setup:
  - Arduino UNO
  - 2x ADXL345 Accelerometers on I2C (SDA=A4, SCL=A5)
  - Both sensors share VCC, GND, SDA, SCL
  - SENSOR 1: SDO connected to GND (I2C address: 0x53)
  - SENSOR 2: SDO connected to 5V (I2C address: 0x1D)
  
  Synchronization Strategy:
  1. Both sensors are initialized with identical settings
  2. Both are read sequentially within the same loop iteration
  3. Data is timestamped with micros() for precision timing
  4. Sample rate is fixed and consistent (50 Hz = 20ms intervals)
  5. CSV output includes timestamp for verification
  
  Important: This ensures both sensors sample at the SAME time with the SAME clock,
             which is critical for structural analysis mode shape calculations.
  
  ==================================================================================
*/

#include <Wire.h>

// ============================================================================
// CONFIGURATION
// ============================================================================

// ADXL345 I2C Addresses
#define ADXL345_ADDR1 0x53  // Sensor 1: SDO to GND
#define ADXL345_ADDR2 0x1D  // Sensor 2: SDO to 5V

// ADXL345 Registers
#define REG_DEVID         0x00  // Device ID (should read 0xE5)
#define REG_POWER_CTL     0x2D  // Power control
#define REG_DATA_FORMAT   0x31  // Data format register
#define REG_DATAX0        0x32  // X-axis data 0
#define REG_DATAX1        0x33  // X-axis data 1
#define REG_DATAY0        0x34  // Y-axis data 0
#define REG_DATAY1        0x35  // Y-axis data 1
#define REG_DATAZ0        0x36  // Z-axis data 0
#define REG_DATAZ1        0x37  // Z-axis data 1
#define REG_FIFO_CTL      0x38  // FIFO control register
#define REG_INT_SOURCE    0x30  // Interrupt source register

// Sampling configuration
#define SAMPLE_RATE_HZ     50      // 50 Hz sampling rate
#define SAMPLE_INTERVAL_MS 20      // 20 ms between samples (1000/50)
#define COLLECTION_TIME_MS 30000   // 30 seconds total
#define BUFFER_SIZE        1500    // Max samples in 30 seconds at 50 Hz

// ============================================================================
// DATA STRUCTURES
// ============================================================================

struct SensorData {
  int16_t x;
  int16_t y;
  int16_t z;
  unsigned long timestamp_us;  // Microsecond timestamp for sync verification
};

struct DualSensorSample {
  SensorData sensor1;
  SensorData sensor2;
  unsigned long sample_time_ms;  // Sample collection time in milliseconds
};

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

bool isRecording = false;
unsigned long recordingStartTime_ms = 0;
unsigned long lastSampleTime_ms = 0;
unsigned int sampleCount = 0;

// Configuration flags
boolean sensor1_connected = false;
boolean sensor2_connected = false;

// ============================================================================
// SETUP
// ============================================================================

void setup() {
  // Initialize serial communication (115200 baud for fast data transfer)
  Serial.begin(115200);
  
  // Wait for serial to stabilize
  delay(1000);
  
  // Initialize I2C
  Wire.begin();
  
  // Print header
  Serial.println("==========================================");
  Serial.println("SYNCHRONIZED DUAL ADXL345 SENSOR SYSTEM");
  Serial.println("==========================================");
  Serial.println("");
  
  // Verify and initialize sensors
  Serial.println("Initializing sensors...");
  delay(100);
  
  sensor1_connected = initializeADXL345(ADXL345_ADDR1, 1);
  delay(100);
  
  sensor2_connected = initializeADXL345(ADXL345_ADDR2, 2);
  delay(100);
  
  Serial.println("");
  Serial.println("Sensor Status:");
  Serial.print("  Sensor 1 (0x53): ");
  Serial.println(sensor1_connected ? "✓ Connected" : "✗ NOT FOUND");
  Serial.print("  Sensor 2 (0x1D): ");
  Serial.println(sensor2_connected ? "✓ Connected" : "✗ NOT FOUND");
  Serial.println("");
  
  if (!sensor1_connected || !sensor2_connected) {
    Serial.println("ERROR: One or both sensors not detected!");
    Serial.println("Check I2C connections and SDO pin configuration");
    while(1);  // Halt
  }
  
  Serial.println("Configuration:");
  Serial.println("  Sampling Rate: 50 Hz");
  Serial.println("  Sample Interval: 20 ms");
  Serial.println("  Range: ±16g");
  Serial.println("  Resolution: Full (13-bit)");
  Serial.println("");
  Serial.println("Ready to record!");
  Serial.println("Send any character via serial to START recording (30 seconds)");
  Serial.println("");
}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {
  // Check for serial input to start recording
  if (Serial.available() > 0) {
    char c = Serial.read();
    if (!isRecording) {
      startRecording();
    }
  }
  
  // Collect data at fixed intervals while recording
  if (isRecording) {
    unsigned long currentTime_ms = millis();
    
    // Check if recording time has exceeded 30 seconds
    if (currentTime_ms - recordingStartTime_ms >= COLLECTION_TIME_MS) {
      stopRecording();
    }
    // Check if it's time for next sample
    else if (currentTime_ms - lastSampleTime_ms >= SAMPLE_INTERVAL_MS) {
      collectSynchronizedSample();
      lastSampleTime_ms = currentTime_ms;
    }
  }
}

// ============================================================================
// RECORDING FUNCTIONS
// ============================================================================

void startRecording() {
  isRecording = true;
  recordingStartTime_ms = millis();
  lastSampleTime_ms = recordingStartTime_ms;
  sampleCount = 0;
  
  Serial.println("");
  Serial.println("==========================================");
  Serial.println("RECORDING STARTED");
  Serial.println("Duration: 30 seconds");
  Serial.println("Expected samples: ~1500");
  Serial.println("==========================================");
  Serial.println("");
  
  // Print CSV header
  Serial.println("Timestamp_ms,S1_X_g,S1_Y_g,S1_Z_g,S2_X_g,S2_Y_g,S2_Z_g");
}

void stopRecording() {
  isRecording = false;
  
  unsigned long totalTime_ms = millis() - recordingStartTime_ms;
  float actualRate = (sampleCount * 1000.0) / totalTime_ms;
  
  Serial.println("");
  Serial.println("==========================================");
  Serial.println("RECORDING STOPPED");
  Serial.print("Total samples: ");
  Serial.println(sampleCount);
  Serial.print("Total time: ");
  Serial.print(totalTime_ms);
  Serial.println(" ms");
  Serial.print("Actual sample rate: ");
  Serial.print(actualRate, 2);
  Serial.println(" Hz");
  Serial.println("==========================================");
  Serial.println("");
  Serial.println("Ready for next recording. Send any character to start...");
  Serial.println("");
}

// ============================================================================
// SYNCHRONIZED DATA COLLECTION
// ============================================================================

void collectSynchronizedSample() {
  // This function ensures BOTH sensors are read at the SAME TIME
  // This is critical to prevent the "Multi-Channel Synchronization Issue"
  
  // Get current timestamp BEFORE reading (for synchronization verification)
  unsigned long sample_timestamp_us = micros();
  unsigned long sample_time_ms = millis() - recordingStartTime_ms;
  
  // Read BOTH sensors sequentially (as fast as possible)
  SensorData s1, s2;
  
  // Read Sensor 1 (address 0x53)
  readADXL345(ADXL345_ADDR1, s1);
  s1.timestamp_us = sample_timestamp_us;
  
  // Read Sensor 2 (address 0x1D) immediately after
  readADXL345(ADXL345_ADDR2, s2);
  s2.timestamp_us = micros();  // Get end time to check timing
  
  // Convert raw values to g-forces
  // ADXL345 scale: ±16g range = 0.004g per LSB
  float gx1 = s1.x * 0.004;
  float gy1 = s1.y * 0.004;
  float gz1 = s1.z * 0.004;
  
  float gx2 = s2.x * 0.004;
  float gy2 = s2.y * 0.004;
  float gz2 = s2.z * 0.004;
  
  // Output in CSV format with timestamp
  Serial.print(sample_time_ms);
  Serial.print(",");
  Serial.print(gx1, 4);
  Serial.print(",");
  Serial.print(gy1, 4);
  Serial.print(",");
  Serial.print(gz1, 4);
  Serial.print(",");
  Serial.print(gx2, 4);
  Serial.print(",");
  Serial.print(gy2, 4);
  Serial.print(",");
  Serial.println(gz2, 4);
  
  sampleCount++;
  
  // Print progress every 50 samples (~1 second at 50Hz)
  if (sampleCount % 50 == 0) {
    // Optional: Print status via Serial (comment out if not needed)
    // Serial.print(".");
  }
}

// ============================================================================
// SENSOR INITIALIZATION & COMMUNICATION
// ============================================================================

boolean initializeADXL345(int address, int sensorNum) {
  // Verify sensor is present by reading device ID
  byte devID = readRegister(address, REG_DEVID);
  
  if (devID != 0xE5) {
    Serial.print("  Sensor ");
    Serial.print(sensorNum);
    Serial.print(" (0x");
    Serial.print(address, HEX);
    Serial.print("): Device ID = 0x");
    Serial.print(devID, HEX);
    Serial.println(" (expected 0xE5)");
    return false;
  }
  
  // Configure data format: ±16g range, full resolution (13-bit)
  writeRegister(address, REG_DATA_FORMAT, 0x0B);
  delay(10);
  
  // Enable measurement mode
  writeRegister(address, REG_POWER_CTL, 0x08);
  delay(10);
  
  // Optional: Configure FIFO for better data integrity
  // FIFO mode bypassed (default) is fine for streaming
  
  return true;
}

void readADXL345(int address, SensorData &data) {
  // Read 6 bytes starting from DATAX0
  Wire.beginTransmission(address);
  Wire.write(REG_DATAX0);
  Wire.endTransmission(false);  // Repeated start
  
  Wire.requestFrom(address, 6);
  
  if (Wire.available() >= 6) {
    // Read X, Y, Z (each is 2 bytes, little-endian)
    byte x_low = Wire.read();
    byte x_high = Wire.read();
    byte y_low = Wire.read();
    byte y_high = Wire.read();
    byte z_low = Wire.read();
    byte z_high = Wire.read();
    
    // Combine bytes (little-endian 16-bit signed values)
    data.x = (int16_t)((x_high << 8) | x_low);
    data.y = (int16_t)((y_high << 8) | y_low);
    data.z = (int16_t)((z_high << 8) | z_low);
  } else {
    // Error reading data
    data.x = 0;
    data.y = 0;
    data.z = 0;
  }
}

byte readRegister(int address, byte reg) {
  Wire.beginTransmission(address);
  Wire.write(reg);
  Wire.endTransmission(false);  // Repeated start
  
  Wire.requestFrom(address, 1);
  if (Wire.available()) {
    return Wire.read();
  }
  return 0xFF;
}

void writeRegister(int address, byte reg, byte value) {
  Wire.beginTransmission(address);
  Wire.write(reg);
  Wire.write(value);
  Wire.endTransmission();
}

// ============================================================================
// END OF SKETCH
// ============================================================================

/*
  TROUBLESHOOTING GUIDE:
  
  1. Sensors not detected:
     - Check I2C wiring (SDA=A4, SCL=A5 on Arduino UNO)
     - Verify pull-up resistors (typically 4.7k ohms on SDA and SCL)
     - Check SDO pin connections (1=5V for 0x1D, 0=GND for 0x53)
     - Try "I2C Scanner" sketch to find actual addresses
  
  2. Bad data / Synchronization issues:
     - Check power supply stability (use 3.3V regulator if needed)
     - Reduce cable length or add shielding
     - Check for loose connections
     - Verify baud rate matches serial monitor (115200)
  
  3. Drifting data or noise:
     - Add capacitors near sensor power pins (0.1µF recommended)
     - Ensure good ground connections
     - Keep sensor away from EMI sources
  
  DATA VALIDATION:
  To verify synchronization is working:
  1. Check that sample rate is ~50 Hz (1500 samples in 30 seconds)
  2. Verify timestamp increments are ~20 ms apart
  3. Look for consistent patterns in both sensors
  4. Use the pre_analysis_validator.py script to check FFT alignment
  
  If you still get "Multi-Channel Synchronization Issue" in analysis:
  1. Check that BOTH sensors are sampled in same loop iteration (they are here!)
  2. Ensure fixed time intervals between samples (20ms = 50Hz)
  3. Verify CSV has identical data length for both sensors (it does here!)
  4. Confirm no gaps or timing jitter in timestamps
*/
