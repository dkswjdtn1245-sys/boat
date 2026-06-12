import time
import sys
import os
import glob
import board
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# ==========================================
# 1. 하드웨어 초기화 및 예외 처리
# ==========================================
# 1-1) DS18B20 수온 센서 커널 드라이버 활성화
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
base_dir = '/sys/bus/w1/devices/'
device_folders = glob.glob(base_dir + '28-*')
device_file = device_folders[0] + '/w1_slave' if device_folders else None

if device_file:
    print("[SUCCESS] DS18B20 수온 센서 인식 완료!")
else:
    print("[WARN] 수온 센서가 연결되지 않았거나 1-Wire 설정이 꺼져 있습니다.")

# 1-2) ADS1115 ADC 컨버터 초기화 (I2C 통신)
try:
    i2c = board.I2C()
    ads = ADS.ADS1115(i2c)
    
    # ★ 에러 해결 포인트: ADS.P0, ADS.P1 대신 직관적인 채널 숫자 0과 1을 바로 대입!
    chan_turb = AnalogIn(ads, 0) # ADS1115의 A0 핀 : 탁도 센서
    chan_tds = AnalogIn(ads, 1)  # ADS1115의 A1 핀 : TDS 센서  
    print("[SUCCESS] ADS1115 ADC 컨버터 통신 성공!")
except Exception as e:
    print(f"[CRITICAL ERROR] ADC 컨버터 연결 실패 (배선 확인 요망): {e}")
    sys.exit(1)

# ==========================================
# 2. 전압 -> 직관적인 수치 변환 함수
# ==========================================

def get_temperature():
    """수온 센서 데이터 읽기"""
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

def convert_turbidity(voltage):
    """야매 세팅 특화 탁도 변환 로직"""
    v_calibrated = min(voltage, 3.3)
    ntu = (3.3 - v_calibrated) * 1200 
    if ntu < 0: ntu = 0.0
    
    if ntu < 50:
        status = "🟢 매우 맑음"
    elif ntu < 300:
        status = "🟡 보통"
    else:
        status = "🔴 탁함"
        
    return ntu, status

def convert_tds(voltage, temperature):
    """TDS 전압 -> PPM 오염도 변환 로직"""
    compensation_coefficient = 1.0 + 0.02 * (temperature - 25.0)
    compensation_voltage = voltage / compensation_coefficient
    
    tds_ppm = (133.33 * (compensation_voltage**3) - 255.86 * (compensation_voltage**2) + 857.39 * compensation_voltage) * 0.5
    if tds_ppm < 0: tds_ppm = 0.0
    
    if tds_ppm < 100:
        tds_status = "정상"
    elif tds_ppm < 400:
        tds_status = "주의"
    else:
        tds_status = "위험"
        
    return tds_ppm, tds_status

# ==========================================
# 3. 실시간 모니터링 반복 루프
# ==========================================
print("\n[START] 수질 3종 야매 통합 테스트 시작 (Ctrl + C 누르면 종료)\n")
print("-" * 70)

try:
    while True:
        current_temp = get_temperature()
        raw_turb_volt = chan_turb.voltage
        raw_tds_volt = chan_tds.voltage
        
        ntu_val, turb_status = convert_turbidity(raw_turb_volt)
        ppm_val, tds_status = convert_tds(raw_tds_volt, current_temp)
        
        print(f"[수온] {current_temp:.1f}°C")
        print(f"[탁도] 원본: {raw_turb_volt:.2f}V ➡️ 변환: {ntu_val:.1f} NTU [{turb_status}]")
        print(f"[TDS ] 원본: {raw_tds_volt:.2f}V ➡️ 변환: {ppm_val:.1f} ppm ({tds_status})")
        print("-" * 70)
        
        time.sleep(0.8)

except KeyboardInterrupt:
    print("\n[STOP] 수질 테스트가 안전하게 마감되었습니다.")
