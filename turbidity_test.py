import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# 1. I2C 버스 및 ADS1115 ADC 모듈 초기화
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# 2. [야매 세팅용 게인 조절] 
# ADS1115 전원이 3.3V이므로, 최대 4.096V까지 읽는 GAIN = 1이 가장 정밀합니다.
ads.gain = 1

# 3. 탁도 센서 신호선(파란선)이 연결된 A0 핀 지정
# ADS.P0 대신 핀 번호를 직접 지정하는 방식으로 수정
chan = AnalogIn(ads, ADS.P0)

print("=========================================")
print("    [야매 세팅] 탁도 센서 무납땜 5분 컷 테스트    ")
print("          종료하려면 Ctrl + C를 누르세요.      ")
print("=========================================")
print("※ 주의: 3.3V 전원 특성상 맑은 물에서는 3.30V 고정입니다.")
print("※ 오염 물질(커피/흙)을 타서 전압이 떨어지는지 확인하세요.")
print("=========================================")
time.sleep(1)

try:
    while True:
        # ADC로부터 raw 값과 변환된 전압(V) 읽기
        # 위에서 선언한 변수명 chan을 사용하도록 수정
        raw_value = chan.value
        voltage = chan.voltage
        
        # 만약 전압이 ADS1115 공급전원(3.3V)을 넘어가면 강제로 3.3V로 표기
        if voltage > 3.30:
            voltage = 3.30
            
        print(f" [측정 중] RAW: {raw_value:<5} | 전압: {voltage:.3f} V")
        
        time.sleep(1)

except KeyboardInterrupt:
    print("\n[안내] 테스트가 안전하게 종료되었습니다.")
