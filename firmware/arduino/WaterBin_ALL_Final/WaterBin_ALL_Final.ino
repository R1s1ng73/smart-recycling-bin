#include <SPI.h>
#include <mcp2515.h>

struct can_frame canMsg;
MCP2515 mcp2515(10);

// 水桶狀態
enum BucketStatus {
  CLEAN_BUCKET_FULL = 0x01,
  CLEAN_BUCKET_EMPTY = 0x02,
  SEWAGE_BUCKET_FULL = 0x03,
  SEWAGE_BUCKET_EMPTY = 0x04
};

// 定義引腳
const int waterSensorPin = 4; // 水感應器引腳
const int sewageSensorPin = 5; // 水感應器引腳
const int relayPin = 3;        // 繼電器引腳
const int buttonPin = 6;       // 按鈕引腳

const uint32_t myCanID = 0x001; // 替換為您的唯一 ID

void setup() {
  pinMode(waterSensorPin, INPUT); // 設定水感應器為輸入
  pinMode(sewageSensorPin, INPUT); // 設定水感應器為輸入
  pinMode(relayPin, OUTPUT);       // 設定繼電器為輸出
  pinMode(buttonPin, INPUT_PULLUP); // 設定按鈕為輸入並啟用內部拉高電阻
  Serial.begin(9600);

   // 設置外部中斷，按鈕按下時觸發
  attachInterrupt(digitalPinToInterrupt(buttonPin), buttonISR, FALLING);
    
  mcp2515.reset();
  mcp2515.setBitrate(CAN_500KBPS, MCP_8MHZ);
  mcp2515.setNormalMode();  
}

  bool waterDetected = digitalRead(waterSensorPin) == LOW;
  bool sewageDetected = digitalRead(sewageSensorPin) == LOW; // 有水時輸出 LOW
  bool buttonPressed = digitalRead(buttonPin) == LOW;      // 按下時輸出 LOW
  bool prev_waterDetected = waterDetected;
  bool prev_sewageDetected = sewageDetected;

void loop() {
  // 讀取水感應器和按鈕的狀態


// 打印當前狀態
  Serial.print("Water Detected: ");
  Serial.print(waterDetected);
  Serial.print(", Sewage Detected: ");
  Serial.print(sewageDetected);
  Serial.print(", Button Pressed: ");
  Serial.println(buttonPressed);
  delay(1000);

  buttonPressed = (digitalRead(buttonPin) == LOW);
  waterDetected = (digitalRead(waterSensorPin) == LOW);
  sewageDetected = (digitalRead(sewageSensorPin) == LOW);
      
  // 如果有水並且按鈕被按下
  if (waterDetected && buttonPressed && !sewageDetected) {
    Serial.println("Starting pump for 3 seconds...");
    // 開啟水泵
    digitalWrite(relayPin, HIGH);
    delay(1000);
    digitalWrite(relayPin, LOW); // 啟動繼電器（抽水）
    delay(3000);


// 繼續檢查按鈕狀態，每 0.5 秒檢查一次
    while (true) {
      // 每 500 毫秒檢查一次
      delay(500);

      // 更新按鈕和水的狀態
      buttonPressed = (digitalRead(buttonPin) == LOW);
      waterDetected = (digitalRead(waterSensorPin) == LOW);
      sewageDetected = (digitalRead(sewageSensorPin) == LOW);

      // 打印當前狀態
      Serial.print("During continuous pumping - Water Detected: ");
      Serial.print(waterDetected);
      Serial.print(", Sewage Detected: ");
      Serial.print(sewageDetected);
      Serial.print(", Button Pressed: ");
      Serial.println(buttonPressed);
      delay(3000);

      // 如果按鈕仍然按下且有水，則啟動水泵 1 秒
      if (buttonPressed && waterDetected && !sewageDetected) {
        ;
      } else {
        // 如果按鈕未按下或水狀態改變，則退出循環
        Serial.println("Pump stopped due to button or water status change.");
        digitalWrite(relayPin, HIGH);
        delay(1000);
        digitalWrite(relayPin, LOW);
        break;
      }
    }
  }

  if(sewageDetected != prev_sewageDetected){
          // 根據水桶狀態設定CAN消息
      

      if (sewageDetected) {
        canMsg.can_id  = 0x036; // 髒水桶ID
        canMsg.can_dlc = 1; // 數據長度
        canMsg.data[0] = SEWAGE_BUCKET_FULL; // 髒水桶已滿
      } else {
        canMsg.can_id  = 0x036; // 髒水桶ID
        canMsg.can_dlc = 1; // 數據長度
        canMsg.data[0] = SEWAGE_BUCKET_EMPTY; // 髒水桶已空
      }

           //發送CAN消息
      mcp2515.sendMessage(&canMsg);
      Serial.print("Message sent: ");
      Serial.println(canMsg.data[0], HEX);
      delay(2000);

    prev_sewageDetected = sewageDetected;
  }
      if(waterDetected != prev_waterDetected){

        if (waterDetected) {
        canMsg.can_id  = 0x0F6; // 乾淨水桶ID
        canMsg.can_dlc = 1; // 數據長度
        canMsg.data[0] = CLEAN_BUCKET_FULL; // 乾淨水桶已滿
      } else {
        canMsg.can_id  = 0x0F6; // 乾淨水桶ID
        canMsg.can_dlc = 1; // 數據長度
        canMsg.data[0] = CLEAN_BUCKET_EMPTY; // 乾淨水桶已空
      }
      mcp2515.sendMessage(&canMsg);
      Serial.print("Message sent: ");
      Serial.println(canMsg.data[0], HEX);
      delay(2000);
      
      prev_waterDetected = waterDetected;

    }
}


  // 按鈕中斷服務例程
void buttonISR() {
  buttonPressed = true; // 設定按鈕被按下的標誌
}
