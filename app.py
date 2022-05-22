from flask import Flask
from flask import render_template
import RPi.GPIO as GPIO
import time
import Adafruit_DHT

sensor = Adafruit_DHT.DHT11

GPIO.setmode(GPIO.BCM) # GPIO핀의 번호 모드 설정
GPIO.setwarnings(False) # 불필요한 warning 제거

app = Flask(__name__)

# 사용할 GPIO핀의 번호를 선정합니다.
TRIG = 23
ECHO = 24
SERVO_PIN = 18        #360도 서보모터
SERVO_WINDOW = 27     #180도 서보모터
button_pin = 14
led_r = 9 
led_g = 10
led_b = 11
pin = 17
led_pin = 4 


# 핀의 입/출력 설정
GPIO.setup(ECHO,GPIO.IN)
GPIO.setup(TRIG,GPIO.OUT)
GPIO.setup(led_pin, GPIO.OUT) 
GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.setup(SERVO_WINDOW, GPIO.OUT)
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(led_r, GPIO.OUT)
GPIO.setup(led_g, GPIO.OUT)
GPIO.setup(led_b, GPIO.OUT)

def led_on(rgb):
    GPIO.output(led_r, GPIO.LOW)
    GPIO.output(led_g, GPIO.LOW)
    GPIO.output(led_b, GPIO.LOW)
    time.sleep(0.2)

    if rgb == "R":
        GPIO.output(led_r, GPIO.HIGH)
    if rgb == "G":
        GPIO.output(led_g, GPIO.HIGH)
    if rgb == "B":
        GPIO.output(led_b, GPIO.HIGH)
    if rgb == "W":
        GPIO.output(led_r, GPIO.LOW)


# PWM 인스턴스 servo 생성, 주파수 50으로 설정 
servo = GPIO.PWM(SERVO_PIN,50)
# PWM 듀티비 0 으로 시작 
servo.start(0)

#Trig핀의 신호를 0으로 출력 
GPIO.output(TRIG, False)
print("Waiting for sensor to settle")

def measure():                  #초음파 센서
    GPIO.output(TRIG, True)     # Triger 핀에  펄스신호를 만들기 위해 1 출력
    time.sleep(0.00001)         # 10µs 딜레이 
    GPIO.output(TRIG, False)
    
    while GPIO.input(ECHO)==0:
        start = time.time()     # Echo 핀 상승 시간 
    while GPIO.input(ECHO)==1:
        stop = time.time()      # Echo 핀 하강 시간 
    
    check_time = stop - start
    distance = (check_time * 34300 )/ 2

    return distance

@app.route("/")
def project():
    return render_template("index.html")

@app.route("/SR-04")
def sr_04():
    try:
        while True:
            distance = measure()
            time.sleep(2)        # 2초 간격으로 센서 측정 

            if distance < 20:    # 출입자가 일정거리 안으로 접근하면 회전문 운영
                print("OPEN!")
                led_on('G')
                servo.ChangeDutyCycle(7.5)

                def button_callback(channel):
                    light_on = False

                    if light_on == False:            # 비상버튼 누르면
                        servo.ChangeDutyCycle(0)     # 회전문 멈춤
                        print("! S O S ! ")
                        for i in range(10):
                            led_on('R')
                            time.sleep(0.5)
                            led_on('W')
                            time.sleep(0.5)
                    light_on = not light_on
                    
                GPIO.add_event_detect(button_pin,GPIO.RISING,callback=button_callback, bouncetime=300)
                while 1:
                    time.sleep(0.0001) 

            else:                                   # 출입자 감지가 느껴지지 않음
                servo.ChangeDutyCycle(0)            # 회전문 미운영
                print("..") 
        return "ok"
    except:
        return "fail"

@app.route("/DHT11")
def dht11():
    servo = GPIO.PWM(SERVO_WINDOW,60)
    servo.start(0)
    try:
        while True:
            h, t = Adafruit_DHT.read_retry(sensor, pin)
            if h is not None and t is not None:
                if t > 23:
                    print("실내 온도가 높아, 환기를 실행합니다")
                    print("현재 온도 = {0:0.1f}*C 습도 = {1:0.1f}%".format(t,h))
                    servo.ChangeDutyCycle(12.5) # 180도
                    time.sleep(3)
                    servo.ChangeDutyCycle(2.5) # 90도
                    time.sleep(3)

                else:
                    print("환기를 완료했습니다.")
                    servo.stop()
                    GPIO.cleanup()
            else:
                print("Read Error")
            time.sleep(1)
        return "ok"
    except:
        return "fail"


if __name__ == "__main__":
    app.run(host="0.0.0.0")
