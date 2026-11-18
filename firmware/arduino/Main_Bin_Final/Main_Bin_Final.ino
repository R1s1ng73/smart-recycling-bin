const int trigPin = 2;    // 超声波传感器的Trig引脚
const int echoPin = 3;    // 超声波传感器的Echo引脚
const int relayPin = 5;    // 控制继电器的引脚



int count = 0;               // 推出的计数
const int maxCount = 3;      // 最大推出次数
unsigned long stableStartTime = 0; // 记录稳定时间的开始
bool isStable = false;        // 状态标志，表示距离是否稳定小于20厘米

#include <SPI.h>
#include <MFRC522.h>
unsigned long previousMillis = 0; // Store the last time the code was run
const long interval = 10000; // Interval set to 10 seconds (10000 milliseconds)

#define SS_PIN 10
#define RST_PIN 9
MFRC522 rfid(SS_PIN, RST_PIN);

#include <Wire.h> // Include the Wire library for I2C
#include <Adafruit_SHT31.h> // Include the Adafruit SHT31 library

//Reading the Pressure Sensor
// Define the pin number for the analog input
const int analogPin = A6;   // Connect your analog device to A0
const int threshold = 860;  // Set your threshold value (0-1023)
bool intterupted = false;


const int smokeSensorPin = A0; // Pin connected to the smoke detector
const int gasSensorPin = A1;   // Pin connected to the gas detector
const int fireSensorPin = A2;  // Pin connected to the fire detector
const int SmokeThreshold = 300; // Set a threshold value for smoke detection
const int GasThreshold = 400;   // Set a threshold value for gas detection
const int FireThreshold = 500;  // Set a threshold value for fire detection

int SmokeValue; // Variable to store the smoke sensor value
int GasValue;   // Variable to store the gas sensor value
int FireValue;  // Variable to store the fire sensor value
float Temperature; // Variable to store temperature value
float Humidity;    // Variable to store humidity value

Adafruit_SHT31 sht31 = Adafruit_SHT31(); // Create an instance of the SHT31 sensor

void setup() {
    pinMode(trigPin, OUTPUT); // 设置Trig引脚为输出
    pinMode(echoPin, INPUT);  // 设置Echo引脚为输入
    pinMode(relayPin, OUTPUT); // 设置继电器引脚为输出
    digitalWrite(relayPin, HIGH);
    Serial.begin(9600); // 启动串口监视器
    SPI.begin();
    rfid.PCD_Init();
    Wire.begin();       // Initialize I2C
    if (!sht31.begin(0x44)) { // Check if the sensor is connected (0x44 is the default address)
         Serial.println("Could not find SHT30 sensor!");
         while (1) delay(10); // Halt if the sensor is not found
     }
    // Attach interrupt to pressure sensor pin

}

void loop() {
   if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
        String rfidID = "";
        for (byte i = 0; i < rfid.uid.size; i++) {
            rfidID += String(rfid.uid.uidByte[i], DEC);
        }
        Serial.println("UID:" + rfidID); // 發送 RFID ID 到 Raspberry Pi
        delay(1000);
    }

    long duration, distance;

    
    // 发送超声波脉冲
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);

    // 读取回声脉冲的持续时间
    duration = pulseIn(echoPin, HIGH);
    
    // 计算距离（单位：厘米）
    distance = (duration * 0.034) / 2;

    // 打印距离
    Serial.print("距离: ");
    Serial.print(distance);
    Serial.println(" cm");

    float fullper = ((44 - distance) / 44) * 100; // Calculate percentage
//    Serial.print("fullper:");
//    Serial.println(fullper);
//    
    unsigned long currentMillis = millis(); // Get the current time

    if (currentMillis - previousMillis >= interval) {
        previousMillis = currentMillis; // Save the last time the code was run

        String FULLlv = "FILL:" + String(fullper); // Combine the string and integer
        Serial.println(FULLlv); // Print the result to the Serial Monitor
        readSmokeSensor(); // Call the function to read the smoke sensor
        readGasSensor();   // Call the function to read the gas sensor
        readFireSensor();  // Call the function to read the fire sensor
        readTemperatureAndHumidity(); // Call the function to read temperature and humidity

    }
    
    // 检查距离是否小于10厘米//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    if (distance < 10) {
        if (!isStable) {
            // 如果距离小于10厘米且状态不稳定，开始计时
            if (stableStartTime == 0) {
                stableStartTime = millis(); // 记录开始时间
            } else if (millis() - stableStartTime >= 5000) {
                // 如果已经稳定小于10厘米5秒
                isStable = true; // 设置状态为稳定
            }
        }
    } else {
        // 如果距离大于10厘米，重置状态
        stableStartTime = 0; // 重置计时
        isStable = false; // 重置稳定状态
    }

    // 当距离稳定小于10厘米时，推出液压杆
    if (isStable && count < maxCount) {
        Serial.println("物体检测到，推出液压杆");
        
        digitalWrite(relayPin, HIGH);
        delay(1000); // Initial activation
        // Start extending the hydraulic rod
        digitalWrite(relayPin, LOW); // 推出液压杆
        unsigned long startTime = millis(); // Record start time
        


        while (millis() - startTime < 20000) { // Extend for 20 seconds
            if (read_Pressure()) {
                Serial.println("压力传感器检测到压力，收缩液压杆");
                digitalWrite(relayPin, HIGH); // Deactivate relay to retract
                delay(1000); // Time for retraction
                digitalWrite(relayPin, LOW); //收缩液压杆
                delay(1000); // Time for retraction
                intterupted = true;
                break; // Exit the while loop if retraction occurs
            }

            // Change logic, if interrupt then dont retract
        }

        if (intterupted == true){
            intterupted = false;
        }else{
            digitalWrite(relayPin, HIGH); // Deactivate relay to retract
            delay(1000); // Time for retraction
            digitalWrite(relayPin, LOW);//收缩液压杆
            delay(1000); // Small delay to avoid busy waiting
        }
        count++; // Increase count
        Serial.print("已推出次数: ");
        Serial.println(count);
    }

    // 如果达到最大推出次数，等待输入
    if (count >= maxCount) {
        Serial.println("已达到最大推出次数，请输入以重置计数。");
        while (true) {
            // 等待用户输入
            if (Serial.available() > 0) {
                char input = Serial.read();
                if (input == 'r') { // 输入 'r' 重置计数
                    count = 0;
                    Serial.println("计数已重置。");
                    break; // 退出循环，返回主循环
                }
            }
        }
    }
    
    delay(500); // 等待0.5秒再进行下一次测量
}

void readSmokeSensor() {
    SmokeValue = analogRead(smokeSensorPin); // Read the smoke detector value
//    Serial.print("Smoke Detector Value: ");
//    Serial.println(SmokeValue);

    if (SmokeValue > SmokeThreshold) {
        Serial.println("Smoke detected!");
    } else {
        Serial.println("No smoke detected.");
    }
}

void readGasSensor() {
    GasValue = analogRead(gasSensorPin); // Read the gas detector value
//    Serial.print("Gas Detector Value: ");
//    Serial.println(GasValue);

    if (GasValue > GasThreshold) {
        Serial.println("Gas detected!");
    } else {
        Serial.println("No gas detected.");
    }
}

void readFireSensor() {
    FireValue = analogRead(fireSensorPin); // Read the fire detector value
//    Serial.print("Fire Detector Value: ");
//    Serial.println(FireValue);

    if (FireValue < FireThreshold) {
//        Serial.println("Fire detected!");
        Serial.println("FIRE:true");
    } else {
//        Serial.println("No fire detected.");
        Serial.println("FIRE:false");
    }
}

void readTemperatureAndHumidity() {
    Temperature = sht31.readTemperature(); // Read temperature
    Humidity = sht31.readHumidity();       // Read humidity

    if (!isnan(Temperature) && !isnan(Humidity)) { // Check if readings are valid
//        Serial.print("Temperature: ");
//        Serial.print(Temperature);
//        Serial.println(" °C");
//        
//        Serial.print("Humidity: ");
//        Serial.print(Humidity);
//        Serial.println(" %");
    } else {
        Serial.println("Failed to read from SHT30 sensor.");
    }
}

int read_Pressure() {
  // Read the analog value from the specified pin
  int sensorValue = analogRead(analogPin);

   Serial.print("A3 Value: ");
   Serial.println(analogRead(analogPin));


  // Determine the digital state based on the threshold
  int digitalState = (sensorValue > threshold) ? HIGH : LOW;

  return digitalState;
}
