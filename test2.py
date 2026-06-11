import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# I2C 초기화
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# 게인 설정: 전압 측정 범위를 설정 (2/3은 최대 6.144V)
ads.gain = 2/3

# 채널 1에 연결된 TDS 센서 (P1 대신 숫자 1 사용)
tds_sensor = AnalogIn(ads, 1)

print("--- TDS 센서 테스트 시작 ---")

try:
    while True:
        # 전압값 읽기
        voltage = tds_sensor.voltage
        
        # 3.3V 구동 시 센서값 보정 (이 계수는 물을 담가보며 조정)
        # 0V 근처에서 튀는 값 방지
        if voltage < 0.05:
            ppm = 0.0
        else:
            # 3.3V 구동 보정: 1.5배~2.0배 정도로 보정
            raw_v = voltage * 1.5 
            # DFRobot 공식 (보정 전압 기반)
            ppm = (133.42 * (raw_v**3) - 255.86 * (raw_v**2) + 857.39 * raw_v) * 0.5
            
        print(f"전압: {voltage:.3f}V | 추정 TDS: {ppm:.1f} ppm")
        time.sleep(0.5)
        
except KeyboardInterrupt:
    print("\n테스트 종료")
