// =======================
//         Sensors
// =======================
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
// BME280
#include <Adafruit_BME280.h>
// SCD 30
#include <Adafruit_SCD30.h>

#define SEALEVELPRESSURE_HPA (1013.25)

// I2C
Adafruit_BME280 bme; 
Adafruit_SCD30  scd30;

// Location
const char* location = "office";

// data storage
char* scd30_json;
unsigned long running_time;
const char* device_id = "co2_box_epaper_v";
// BME280
float bme_temp_last;
float bme_temp_adjt = -1.1;
float bme_hum_last;
float bme_hum_adjt = 0;
float bme_altitude_last;
float bme_altitude_adjt = 0;
float bme_pressure_last;
float bme_pressure_adjt = 0;
// SCD30
float scd30_temp_last;
float scd30_temp_adjt = -3.1;
float scd30_hum_last;
float scd30_hum_adjt = 0;
float scd30_co2_last;
float scd30_co2_adjt = 0;

// =======================
//       E-Paper
// =======================
// Hello Screen
const char hello_world[] = "Hello World !";
const char hello_author[] = "hqrrr";
const char hello_date[] = "Jan. 2025";

// Sensor data
char bme_temp[50];
char bme_hum[50];
char bme_altitude[50];
char bme_pressure[50];
char scd30_temp[50];
char scd30_hum[50];
char scd30_co2[50];

#define ENABLE_GxEPD2_GFX 0

#include <GxEPD2_BW.h>

#include <Fonts/FreeMono9pt7b.h>
#include <Fonts/FreeMonoBold9pt7b.h>
#include <Fonts/FreeMonoBold12pt7b.h>
#include <Fonts/FreeMonoBold18pt7b.h>
#include <Fonts/FreeMonoBold24pt7b.h>

// select the display constructor line in one of the following files (old style):
#include "GxEPD2_display_selection.h"
//#include "GxEPD2_display_selection_added.h"
//#include "GxEPD2_display_selection_more.h" // private

// or select the display class and display driver class in the following file (new style):
//#include "GxEPD2_display_selection_new_style.h"

#if !defined(__AVR) && !defined(_BOARD_GENERIC_STM32F103C_H_) && !defined(ARDUINO_BLUEPILL_F103C8)
#include "bitmaps/Bitmaps400x300.h" // 4.2"  b/w
#if defined(ESP8266) || defined(ESP32) || defined(ARDUINO_ARCH_RP2040)
#endif
#if defined(ESP32)
#include "bitmaps/Bitmaps1304x984.h" // 12.48" b/w
#endif
#else
#include "bitmaps/Bitmaps400x300.h" // 4.2"  b/w // not enough code space
#include "bitmaps/Bitmaps3c400x300.h" // 4.2"  b/w/r // not enough code space
#endif

#if defined(ARDUINO_ARCH_RP2040) && defined(ARDUINO_RASPBERRY_PI_PICO)
// SPI pins used by GoodDisplay DESPI-PICO. note: steals standard I2C pins PIN_WIRE_SDA (6), PIN_WIRE_SCL (7)
// uncomment next line for use with GoodDisplay DESPI-PICO.
arduino::MbedSPI SPI0(4, 7, 6); // need be valid pins for same SPI channel, else fails blinking 4 long 4 short
#endif


// =======================
//         SETUP
// =======================
void setup()
{
  Serial.begin(115200);
  delay(500);
  // -----------------------
  //       ini sensors
  // -----------------------
  Serial.println("========= Sensors ========");
  Serial.println("setup...");
  delay(200);
  // BME280 ini
  iniBME280();
  delay(100);

  // SCD30 ini
  iniSCD30();
  delay(100);

  Serial.println("setup done");

  // -----------------------
  //       ini e-paper
  // -----------------------
  Serial.println("========= E Paper ========");
  Serial.println("setup...");
  delay(100);
  display.init(115200); // default 10ms reset pulse, e.g. for bare panels with DESPI-C02
  
  // first update should be full refresh
  helloWorld();
  delay(3000);
  display.powerOff();
  Serial.println("setup done");
  
  Serial.println("==========================");
}

// =======================
//          LOOP
// =======================
void loop()
{
  // refresh full menu page
  mainMenu();
  output_json();
  delay(5000);

  // refresh data
  int i = 0;
  while(i < 200){
    // update device running time
    running_time = millis();
    // read sensor data
    readBME280();
    readSCD30();
    // partial refresh data
    updateMenu();
    // output data in json format
    output_json();
    // count + 1
    i += 1;
    delay(5000);
  }
}

// =======================
//       Functions
// =======================

void iniBME280() {
  Serial.println(F("BME280 test!"));

  if (!bme.begin(0x76)) {
      Serial.println("Failed to find BME280 chip");
      while (1) { delay(10); }
  }
  Serial.println("BME280 Found!");
  Serial.println("");
}

void iniSCD30() {
  Serial.println("SCD30 test!");
  if (!scd30.begin(0x61)) {
    Serial.println("Failed to find SCD30 chip");
    while (1) { delay(10); }
  }
  Serial.println("SCD30 Found!");
  Serial.println("");

  Serial.print("SCD30 Measurement Interval: "); Serial.print(scd30.getMeasurementInterval()); Serial.println(" seconds");
  Serial.println("");
}

void readBME280() {
  bme_temp_last = bme.readTemperature() + bme_temp_adjt; // degC
  bme_hum_last = bme.readHumidity() + bme_hum_adjt; // %
  bme_altitude_last = bme.readAltitude(SEALEVELPRESSURE_HPA) + bme_altitude_adjt; // m
  bme_pressure_last = bme.readPressure() / 100.0F + bme_pressure_adjt; // hPa 
  
}

void readSCD30() {
  if (scd30.dataReady()){
//    Serial.println("SCD30 Data updated!");
    if (!scd30.read()){ Serial.println("Error reading sensor data"); return; }
    scd30_temp_last = scd30.temperature + scd30_temp_adjt; // degC
    scd30_hum_last = scd30.relative_humidity + scd30_hum_adjt; // %
    scd30_co2_last = scd30.CO2 + scd30_co2_adjt; // ppm 
  }

}

void output_json() {
  Serial.print("{");
    Serial.print("\"Device\":\"");Serial.print(device_id);Serial.print("\",");
    Serial.print("\"Location\":\"");Serial.print(location);Serial.print("\",");
    Serial.print("\"Time\":");Serial.print(running_time);Serial.print(",");
    Serial.print("\"Data\":[");
      Serial.print("{");
        Serial.print("\"Sensor\":\"BME280\",");
        Serial.print("\"Value\":{");
          Serial.print("\"Temperature\":");Serial.print(bme_temp_last);Serial.print(","); // degC
          Serial.print("\"Humidity\":");Serial.print(bme_hum_last);Serial.print(","); // %
          Serial.print("\"Pressure\":");Serial.print(bme_pressure_last);Serial.print(","); //hPa
          Serial.print("\"Approx. Altitude\":");Serial.print(bme_altitude_last); //m
        Serial.print("}");
      Serial.print("},{");
        Serial.print("\"Sensor\":\"SCD30\",");
        Serial.print("\"Value\":{");
          Serial.print("\"Temperature\":");Serial.print(scd30_temp_last);Serial.print(","); // degC
          Serial.print("\"Humidity\":");Serial.print(scd30_hum_last);Serial.print(","); // %
          Serial.print("\"CO2\":");Serial.print(scd30_co2_last); //ppm
        Serial.print("}");
      Serial.print("}");
    Serial.print("]");
  Serial.println("}");

}

void helloWorld()
{
  display.setRotation(1);
  display.setFont(&FreeMonoBold12pt7b);
  display.setTextColor(GxEPD_BLACK);
  display.setFullWindow();
  display.firstPage();
  do
  {
    display.fillScreen(GxEPD_WHITE);
    display.setCursor(50, 70);
    display.print(hello_world);
    display.setFont(&FreeMonoBold9pt7b);
    display.setCursor(50, 180);
    display.print(hello_author);
    display.setCursor(50, 220);
    display.print(hello_date);
  }
  while (display.nextPage());
}

void mainMenu()
{
  display.setFont(&FreeMonoBold9pt7b);
  display.setTextColor(GxEPD_BLACK);
  display.setFullWindow();
  display.firstPage();
  do
  {
    display.fillScreen(GxEPD_WHITE);
    // BME280
    // 01 Text
    display.setFont(&FreeMono9pt7b);
    display.setCursor(15, 45);
    display.print("Sensor BME280");
    // Temperature
    // 01 Text
    display.setFont(&FreeMonoBold9pt7b);
    display.setCursor(15, 75);
    display.print("Temp [degC]:");
    // 02 Data
    display.setFont(&FreeMonoBold18pt7b);
    display.setCursor(180, 75);
    sprintf(bme_temp, "%d.%01d", (int)bme_temp_last, (int)(bme_temp_last*10)%10);
    display.print(bme_temp);
    
    // Humidity
    // 01 Text
    display.setFont(&FreeMonoBold9pt7b);
    display.setCursor(15, 105);
    display.print("Humidity [%]:");
    // 02 Data
    display.setFont(&FreeMonoBold18pt7b);
    display.setCursor(180, 105);
    sprintf(bme_hum, "%d.%01d", (int)bme_hum_last, (int)(bme_hum_last*10)%10);
    display.print(bme_hum);


    // Altitude
    // 01 Text
    display.setFont(&FreeMonoBold9pt7b);
    display.setCursor(15, 135);
    display.print("Altitude [m]:");
    // 02 Data
    display.setFont(&FreeMonoBold12pt7b);
    display.setCursor(180, 135);
    sprintf(bme_altitude, "%d", (int)bme_altitude_last);
    display.print(bme_altitude);


    // Air pressure
    // 01 Text
    display.setFont(&FreeMonoBold9pt7b);
    display.setCursor(15, 165);
    display.print("P [hPa]:");
    // 02 Data
    display.setFont(&FreeMonoBold12pt7b);
    display.setCursor(180, 165);
    sprintf(bme_pressure, "%d", (int)bme_pressure_last);
    display.print(bme_pressure);
 
    
    // SCD30
    // 01 Text
    display.setFont(&FreeMono9pt7b);
    display.setCursor(15, 225);
    display.print("Sensor SCD30");
    
    // CO2
    // 01 Text
    display.setFont(&FreeMonoBold9pt7b);
    display.setCursor(15, 255);
    display.print("CO2 [ppm]:");
    // 02 Data
    display.setFont(&FreeMonoBold24pt7b);
    display.setCursor(160, 255);
    sprintf(scd30_co2, "%d%", (int)scd30_co2_last);
    display.print(scd30_co2);


    // Air Quality
    // 01 Text
    display.setFont(&FreeMonoBold9pt7b);
    display.setCursor(15, 285);
    display.print("Air Quality:");
    // 02 Data
    display.setFont(&FreeMonoBold12pt7b);
    display.setCursor(160, 285);
    if (scd30_co2_last < 1000){
      display.print("Good!");
    }
    else if (scd30_co2_last < 1500){
      display.print("Moderate");
    }
    else {
      display.print("Unhealthy");
    }

    // Temperature
    // 01 Text
    display.setFont(&FreeMonoBold9pt7b);
    display.setCursor(15, 315);
    display.print("Temp [degC]:");
    // 02 Data
    display.setFont(&FreeMonoBold12pt7b);
    display.setCursor(160, 315);
    sprintf(scd30_temp, "%d.%01d", (int)scd30_temp_last, (int)(scd30_temp_last*10)%10);
    display.print(scd30_temp);

    
    // Humidity
    // 01 Text
    display.setFont(&FreeMonoBold9pt7b);
    display.setCursor(15, 345);
    display.print("Humidity [%]:");
    // 02 Data
    display.setFont(&FreeMonoBold12pt7b);
    display.setCursor(160, 345);
    sprintf(scd30_hum, "%d.%01d", (int)scd30_hum_last, (int)(scd30_hum_last*10)%10);
    display.print(scd30_hum);

  }
  while (display.nextPage());
}

void updateMenu()
{
  display.setPartialWindow(160, 0, 150, 400); // x, y, width, height
  display.setFont(&FreeMonoBold18pt7b);
  display.setTextColor(GxEPD_BLACK);
  display.firstPage();
  do
  {
    display.fillScreen(GxEPD_WHITE);
    // BME280
    // Temperature
    display.setFont(&FreeMonoBold18pt7b);
    display.setCursor(180, 75);
    sprintf(bme_temp, "%d.%01d", (int)bme_temp_last, (int)(bme_temp_last*10)%10);
    display.print(bme_temp);
    
    // Humidity
    display.setFont(&FreeMonoBold18pt7b);
    display.setCursor(180, 105);
    sprintf(bme_hum, "%d.%01d", (int)bme_hum_last, (int)(bme_hum_last*10)%10);
    display.print(bme_hum);


    // Altitude
    display.setFont(&FreeMonoBold12pt7b);
    display.setCursor(180, 135);
    sprintf(bme_altitude, "%d", (int)bme_altitude_last);
    display.print(bme_altitude);


    // Air pressure
    display.setFont(&FreeMonoBold12pt7b);
    display.setCursor(180, 165);
    sprintf(bme_pressure, "%d", (int)bme_pressure_last);
    display.print(bme_pressure);
 
    
    // SCD30
    display.setFont(&FreeMono9pt7b);
    display.setCursor(15, 225);
    display.print("Sensor SCD30");
    
    // CO2
    display.setFont(&FreeMonoBold24pt7b);
    display.setCursor(160, 255);
    sprintf(scd30_co2, "%d%", (int)scd30_co2_last);
    display.print(scd30_co2);


    // Air Quality
    display.setFont(&FreeMonoBold12pt7b);
    display.setCursor(160, 285);
    if (scd30_co2_last < 1000){
      display.print("Good!");
    }
    else if (scd30_co2_last < 1500){
      display.print("Moderate");
    }
    else {
      display.print("Unhealthy");
    }

    // Temperature
    display.setFont(&FreeMonoBold12pt7b);
    display.setCursor(160, 315);
    sprintf(scd30_temp, "%d.%01d", (int)scd30_temp_last, (int)(scd30_temp_last*10)%10);
    display.print(scd30_temp);

    
    // Humidity
    display.setFont(&FreeMonoBold12pt7b);
    display.setCursor(160, 345);
    sprintf(scd30_hum, "%d.%01d", (int)scd30_hum_last, (int)(scd30_hum_last*10)%10);
    display.print(scd30_hum);
  }
  while (display.nextPage());
}
