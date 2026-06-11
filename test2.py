import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# I2C 버스 및 ADS1115 초기화
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1

# ADS.P0 대신 숫자 0, 1, 2, 3을 직접 대입합니다.
ch0 = AnalogIn(ads, 0)
ch1 = AnalogIn(ads, 1)
ch2 = AnalogIn(ads, 2)
ch3 = AnalogIn(ads, 3)

print("====================================================")
print("  ADS1115 전체 채널 스캔 시작 (GND를 찔러보세요!)  ")
print("====================================================")

try:
    while True:
        # 네 채널의 전압 실시간 출력
        print(f"[A0]: {ch0.voltage:.3f}V  |  [A1]: {ch1.voltage:.3f}V  |  [A2]: {ch2.voltage:.3f}V  |  [A3]: {ch3.voltage:.3f}V")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n종료되었습니다.")
