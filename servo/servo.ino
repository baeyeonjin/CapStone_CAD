#include <Servo.h>
#include <SoftwareSerial.h>
Servo sm;
int n = 0;
int i = 0;
int servor = 9;                                                                                       

SoftwareSerial mySerial(10, 11);
void setup() {
  mySerial.begin(9600);
  Serial.begin(9600);

  //sm.write(90); //90도(중심각) 각도로 회전
  //pinMode(servor, OUTPUT);
}
void loop() {
  if(mySerial.available())
  {
    char g = mySerial.read();

       if(g=='y')
       {
        sm.attach(servor);
        sm.write(0);
        for(n=0;n<2;n++){
        for(i=0; i<=125; i++)
        {
             sm.write(i); //180도로 회전
             delay(2);
        }

        for(i; i>=0; i--)
        {
             sm.write(i); //180도로 회전
             delay(2);
        }
         }
         sm.detach();
       }
       
     }
}
