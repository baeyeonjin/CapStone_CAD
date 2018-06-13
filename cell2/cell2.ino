#include "HX711.h"
#include <SoftwareSerial.h>
#define calibration_factor -176900 //This value is obtained using the SparkFun_HX711_Calibration sketch
#define DOUT  A1
#define CLK  A0
int kg=0;
HX711 scale(DOUT, CLK);
SoftwareSerial mySerial(10, 11);

void setup() {
  mySerial.begin(9600);
  Serial.begin(9600);
  scale.set_scale(calibration_factor); //This value is obtained by using the SparkFun_HX711_Calibration sketch
  scale.tare(); //Assuming there is no weight on the scale at start up, reset the scale to 0

}

void loop() {

 if(Serial.available())
 {
  if(Serial.read()==0)
  {

  kg =  (scale.get_units()*0.453592*1000*-1);
  
  if(kg<=10)
  {
    mySerial.write('y');
  }
    Serial.println(kg);

  
  
 }
}
}
