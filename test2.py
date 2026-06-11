import time
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c) # ADS.ADS1115(i2c) 대신 이것으로 변경
ads.gain = 2/3

# 채널 접근을 아래와 같이 다시 시도해 봐!
tds_sensor = AnalogIn(ads, 1) # P1 대신 숫자 1을 넣으면 대부분의 버전에서 다 해결됨

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
