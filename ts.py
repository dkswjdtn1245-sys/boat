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
    
    # 핀 매칭 안내: A0 = 탁도 센서, A1 = TDS 센서
    chan_turb = AnalogIn(ads, ADS.P0) 
    chan_tds = AnalogIn(ads, ADS.P1)  
    print("[SUCCESS] ADS1115 ADC 컨버터 통신 성공!")
except Exception as e:
    print(f"[CRITICAL ERROR] ADC 컨버터 연결 실패 (배선 확인 요망): {e}")
    sys.exit(1)

# ==========================================
# 2. 전압 -> 직관적인 수치 변환 함수
# ==========================================

def get_temperature():
    """수온 센서 데이터 읽기"""
    if not device_file: return 25.0  # 에러 시 기본값
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
    """
    [야매 세팅 특화 탁도 변환 로직]
    현재 ADS1115가 3.3V 전원을 먹고 있으므로, 맑은 물(원래 4.2V)을 넣어도 3.3V로 고정(Capped)됩니다.
    따라서 3.3V를 '0 NTU(완전 맑음)'로 잡고, 오염되어 전압이 떨어질수록 NTU 수치가 올라가게 세팅했습니다.
    """
    # 3.3V 전원 컷오프 한계 보정
    v_calibrated = min(voltage, 3.3)
    
    # 전압이 낮아질수록 탁도(NTU)는 올라감 (야매 선형 보정 수식)
    ntu = (3.3 - v_calibrated) * 1200 
    if ntu < 0: ntu = 0.0
    
    # 직관적인 수질 상태 판단
    if ntu < 50:
        status = "🟢 매우 맑음 (수돗물 수준)"
    elif ntu < 300:
        status = "🟡 보통 (일반 강물 수준)"
    else:
        status = "🔴 탁함 (흙탕물/오염수 수준)"
        
    return ntu, status

def convert_tds(voltage, temperature):
    """
    [TDS 전압 -> PPM 오염도 변환 로직]
    기본 DFROBOT 수식을 적용하되, 온도 보정을 결합하여 실제 ppm 수치로 환산합니다.
    """
    # 온도 보정 계수 계산
    compensation_coefficient = 1.0 + 0.02 * (temperature - 25.0)
    compensation_voltage = voltage / compensation_coefficient
    
    # 전압 -> TDS (ppm) 환산 3차 수식
    tds_ppm = (133.33 * (compensation_voltage**3) - 255.86 * (compensation_voltage**2) + 857.39 * compensation_voltage) * 0.5
    if tds_ppm < 0: tds_ppm = 0.0
    
    # TDS 기준치 판단
    if tds_ppm < 100:
        tds_status = "정상 (깨끗한 물)"
    elif tds_ppm < 400:
        tds_status = "주의 (이물질 많음)"
    else:
        tds_status = "위험 (식수 불가/오염)"
        
    return tds_ppm, tds_status

# ==========================================
# 3. 실시간 모니터링 반복 루프
# ==========================================
print("\n[START] 수질 3종 야매 통합 테스트 시작 (Ctrl + C 누르면 종료)\n")
print("-" * 70)

try:
    while True:
        # 1) 쌩 데이터(전압 및 온도) 읽기
        current_temp = get_temperature()
        raw_turb_volt = chan_turb.voltage
        raw_tds_volt = chan_tds.voltage
        
        # 2) 직관적인 수치로 가공 변환
        ntu_val, turb_status = convert_turbidity(raw_turb_volt)
        ppm_val, tds_status = convert_tds(raw_tds_volt, current_temp)
        
        # 3) 터미널 창에 보기 좋게 출력
        print(f"[수온] {current_temp:.1f}°C")
        print(f"[탁도] 원본: {raw_turb_volt:.2f}V ➡️ 변환: {ntu_val:.1f} NTU [{turb_status}]")
        print(f"[TDS ] 원본: {raw_tds_volt:.2f}V ➡️ 변환: {ppm_val:.1f} ppm ({tds_status})")
        print("-" * 70)
        
        time.sleep(0.8)  # 0.8초마다 화면 갱신

except KeyboardInterrupt:
    print("\n[STOP] 수질 테스트가 안전하게 마감되었습니다.")
