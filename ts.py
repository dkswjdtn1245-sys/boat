import time
import sys
import os
import glob
import board
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# ==========================================
# 1. 하드웨어 초기화
# ==========================================
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
base_dir = '/sys/bus/w1/devices/'
device_folders = glob.glob(base_dir + '28-*')
device_file = device_folders[0] + '/w1_slave' if device_folders else None

try:
    i2c = board.I2C()
    ads = ADS.ADS1115(i2c)
    chan_turb = AnalogIn(ads, 0) # A0: 탁도
    chan_tds = AnalogIn(ads, 1)  # A1: TDS 
except Exception as e:
    print(f"[ERROR] ADC 통신 실패: {e}")
    sys.exit(1)

# ==========================================
# 2. 공기 중 테스트 전용 판단 함수
# ==========================================

def get_temperature():
    if not device_file: return 25.0
    try:
        with open(device_file, 'r') as f:
            lines = f.readlines()
        if lines[0].strip().endswith('YES'):
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                return float(lines[1][equals_pos+2:]) / 1000.0
    except:
        pass
    return 25.0

def test_turbidity(voltage):
    """탁도 센서: 허공(빛 통과) vs 가림막(빛 차단) 판단"""
    # 전압이 높으면(3V 이상) 빛이 통과 중, 전압이 훅 떨어지면 무언가 가린 것
    if voltage > 3.0:
        return "⚪ 대기중 (빛 100% 통과)"
    else:
        return f"🔴 가림막 감지! (빛 차단됨, 변환 NTU: {(3.3 - voltage) * 1200:.0f})"

def test_tds(voltage):
    """TDS 센서: 허공(0V) vs 가림막/손 접촉(전압 상승) 판단"""
    # 공기 중에서는 저항이 무한대라 0.1V 미만. 
    # 손으로 만지거나 캡(가림막)을 씌워 미세 전류가 통하면 전압이 튐.
    if voltage < 0.15:
        return "⚪ 대기중 (개방됨)"
    else:
        # 전압이 살짝이라도 튀면 접촉으로 판단
        return f"🔴 접촉/캡 감지! (미세 전류 흐름)"

# ==========================================
# 3. 실시간 모니터링 반복 루프
# ==========================================
print("\n[START] 🛠️ 공기 중(Dry Test) 센서 반응 테스트 가동\n")
print("-" * 65)

try:
    while True:
        current_temp = get_temperature()
        raw_turb_volt = chan_turb.voltage
        raw_tds_volt = chan_tds.voltage
        
        # 수온 상태 판단 (손으로 쥐면 온도가 28도 이상으로 올라감)
        if current_temp > 28.0:
            temp_status = "🔴 체온 감지! (온도 상승 중)"
        else:
            temp_status = "⚪ 실온 상태"

        # 화면 출력
        print(f"[수온 센서] {current_temp:.1f}°C \t➡️ {temp_status}")
        print(f"[탁도 센서] {raw_turb_volt:.2f} V \t➡️ {test_turbidity(raw_turb_volt)}")
        print(f"[TDS  센서] {raw_tds_volt:.2f} V \t➡️ {test_tds(raw_tds_volt)}")
        print("-" * 65)
        
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n[STOP] 테스트를 종료합니다.")
