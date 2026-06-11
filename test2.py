import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# 1. I2C 버스 초기화
i2c = busio.I2C(board.SCL, board.SDA)

# 2. ADS1115 객체 생성
ads = ADS.ADS1115(i2c)

# 3. 게인(Gain) 설정 (3.3V 전원 환경에 맞춤)
ads.gain = 1

# 4. 아날로그 입력 채널 설정 (A0 핀을 숫자 0으로 직접 지정)
chan = AnalogIn(ads, 0)

print("==========================================")
print("  TDS 센서 전압 측정 시작 (종료: Ctrl+C)  ")
print("==========================================")

try:
    while True:
        # 실제 변환된 전압 값 (V) 읽기
        voltage = chan.voltage
        
        print(f"현재 TDS 센서 출력 전압: {voltage:.3f} V")
        
        # 1초 간격으로 반복 측정
        time.sleep(1)

except KeyboardInterrupt:
    print("\n사용자에 의해 측정이 종료되었습니다.")
