import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# 1. I2C 버스 및 ADS1115 초기화
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# 2. 게인 설정 (전압 범위)
ads.gain = 2/3

# 3. A1 핀에 연결된 TDS 센서 설정
tds_sensor = AnalogIn(ads, ADS.P1)

def get_tds_value(analog_in):
    # 3.3V 구동으로 인한 신호 감소 보정 (이 계수는 실험하며 조절 가능)
    # 현재는 안전하게 1.5배 보정해둠
    compensated_voltage = analog_in.voltage * 1.5
    
    # 25°C 기준 표준 TDS 계산 공식
    # 전압이 0V면 TDS도 0ppm
    if compensated_voltage <= 0:
        return 0.0, compensated_voltage
    
    # DFRobot 표준 변환 공식 적용
    tds_val = (133.42 * (compensated_voltage ** 3) - 
               255.86 * (compensated_voltage ** 2) + 
               857.39 * compensated_voltage) * 0.5
               
    return max(0.0, tds_val), compensated_voltage

print("--- TDS 센서(A1) 테스트 시작 ---")
try:
    while True:
        tds, volt = get_tds_value(tds_sensor)
        print(f"전압: {volt:.3f}V | 추정 TDS: {tds:.1f} ppm")
        time.sleep(1)
except KeyboardInterrupt:
    print("\n테스트 종료")
