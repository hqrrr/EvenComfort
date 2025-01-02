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
const char* device_id = "co2_box";
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
  Serial.println("==========================");
}

// =======================
//          LOOP
// =======================
void loop()
{
  // read sensor data
  readBME280();
  readSCD30();
  // output data in json format
  output_json();
  // 5s interval
  delay(5000);
  
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
