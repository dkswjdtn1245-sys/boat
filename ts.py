import time
import sys
import os
import glob
import board
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# ==========================================
# 1. 하드웨어 초기화 (완전 독립형)
# ==========================================
# 1-1) 수온 센서 초기화
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
base_dir = '/sys/bus/w1/devices/'
device_folders = glob.glob(base_dir + '28-*')
device_file = device_folders[0] + '/w1_slave' if device_folders else None

# 1-2) ADC 컨버터 초기화 (없어도 안 꺼지게 세팅!)
ads_connected = False
try:
    i2c = board.I2C()
    ads = ADS.ADS1115(i2c)
    chan_turb = AnalogIn(ads, 0) # A0: 탁도
    chan_tds = AnalogIn(ads, 1)  # A1: TDS 
    ads_connected = True
except Exception as e:
    print(f"[WARN] ADC 컨버터를 찾을 수 없습니다. 탁도/TDS는 건너뜁니다. ({e})")

# ==========================================
# 2. 공기 중 테스트 전용 판단 함수
# ==========================================

def get_temperature():
    if not device_file: return None  # 연결 안 되면 None 반환
    try:
        with open(device_file, 'r') as f:
            lines = f.readlines()
        if lines[0].strip().endswith('YES'):
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                return float(lines[1][equals_pos+2:]) / 1000.0
    except:
        pass
    return None

def test_turbidity(voltage):
    if voltage > 3.0:
        return "⚪ 대기중 (빛 100% 통과)"
    else:
        return f"🔴 가림막 감지! (변환 NTU: {(3.3 - voltage) * 1200:.0f})"

def test_tds(voltage):
    if voltage < 0.15:
        return "⚪ 대기중 (개방됨)"
    else:
        return f"🔴 접촉/캡 감지! (미세 전류 흐름)"

# ==========================================
# 3. 실시간 모니터링 반복 루프
# ==========================================
print("\n[START] 🛠️ 공기 중(Dry Test) 완전 독립형 테스트 가동\n")
print("-" * 65)

try:
    while True:
        # 수온 센서 처리
        current_temp = get_temperature()
        if current_temp is not None:
            temp_status = "🔴 체온 감지! (온도 상승 중)" if current_temp > 28.0 else "⚪ 실온 상태"
            print(f"[수온 센서] {current_temp:.1f}°C \t➡️ {temp_status}")
        else:
            print("[수온 센서] ❌ 연결 안 됨")

        # 탁도 & TDS 센서 처리 (ADS1115가 꽂혀있을 때만)
        if ads_connected:
            raw_turb_volt = chan_turb.voltage
            raw_tds_volt = chan_tds.voltage
            print(f"[탁도 센서] {raw_turb_volt:.2f} V \t➡️ {test_turbidity(raw_turb_volt)}")
            print(f"[TDS  센서] {raw_tds_volt:.2f} V \t➡️ {test_tds(raw_tds_volt)}")
        else:
            print("[탁도 센서] ❌ ADC(보라색 칩) 연결 안 됨")
            print("[TDS  센서] ❌ ADC(보라색 칩) 연결 안 됨")
            
        print("-" * 65)
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n[STOP] 테스트를 종료합니다.")
