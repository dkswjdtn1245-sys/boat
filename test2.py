import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
ads.gain = 1

# 4개 채널을 모두 정의합니다.
ch0 = AnalogIn(ads, ADS.P0)
ch1 = AnalogIn(ads, ADS.P1)
ch2 = AnalogIn(ads, ADS.P2)
ch3 = AnalogIn(ads, ADS.P3)

print("====================================================")
print("  ADS1115 전체 채널 스캔 시작 (GND를 찔러보세요!)  ")
print("====================================================")

try:
    while True:
        # 네 채널의 전압을 한 줄로 출력
        print(f"[A0]: {ch0.voltage:.3f}V  |  [A1]: {ch1.voltage:.3f}V  |  [A2]: {ch2.voltage:.3f}V  |  [A3]: {ch3.voltage:.3f}V")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n종료되었습니다.")
