import time
import board
import busio
import serial
import os
import glob
import socket

# ==========================================
# 📡 1. 랩뷰 UDP 통신 세팅
# ==========================================
UDP_IP = "10.242.92.169"  # 노트북(랩뷰) IP
UDP_PORT = 8080
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("🚀 관제 시스템 및 하드웨어 초기화 시작...")

# ==========================================
# 🛠️ 2. 하드웨어 센서 및 모터 초기화
# ==========================================
i2c = busio.I2C(board.SCL, board.SDA)

# 모터 초기화
try:
    from adafruit_pca9685 import PCA9685
    pca = PCA9685(i2c)
    pca.frequency = 50
    print("✅ 모터 드라이버 연결 성공")
except: 
    print("❌ 모터 드라이버 연결 실패")

def set_motor(ch13_pwm, ch15_pwm):
    if 'pca' not in globals(): return
    pca.channels[13].duty_cycle = int((ch13_pwm / 20000) * 65535)
    pca.channels[15].duty_cycle = int((ch15_pwm / 20000) * 65535)

print("⏳ 모터 초기화 진행 중... (삐-빅 소리 대기)")
set_motor(1750, 1750)
time.sleep(3)

# 수온 센서 세팅
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
base_dir = '/sys/bus/w1/devices/'
try:
    device_file = glob.glob(base_dir + '28*')[0] + '/w1_slave'
except:
    device_file = None

def read_temp():
    if device_file is None: return 25.0
    try:
        with open(device_file, 'r') as f: lines = f.readlines()
        if lines[0].strip()[-3:] == 'YES':
            idx = lines[1].find('t=')
            if idx != -1: return float(lines[1][idx+2:]) / 1000.0
    except: pass
    return 25.0

# 🌟 ADS1115 및 수질 센서(탁도, TDS) 세팅 추가 🌟
try:
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    ads = ADS.ADS1115(i2c)
    turb_sensor = AnalogIn(ads, 0)  # A0 핀: 탁도
    tds_sensor = AnalogIn(ads, 1)   # A1 핀: TDS
    print("✅ ADS1115 및 수질 센서 연결 성공")
except Exception as e:
    ads = None
    print(f"❌ ADS1115 연결 실패: {e}")

# 🌟 수질 데이터 변환 함수 (5V 표준식 적용) 🌟
# ==========================================

def get_turbidity_ntu(raw_voltage):
    # 3.3V 보정 계수(* 1.5) 완전 삭제됨! 읽어온 전압(raw_voltage)을 그대로 사용합니다.
    if raw_voltage < 2.5:
        return 3000.0  # 전압이 너무 낮으면 최대 탁도(매우 탁함)
    elif raw_voltage > 4.2:
        return 0.0     # 전압이 4.2V 이상이면 맑은 물
    else:
        # DFRobot 탁도 센서 5V 표준 변환식
        ntu = -1120.4 * (raw_voltage**2) + 5742.3 * raw_voltage - 4353.8
        return max(0.0, ntu)

def get_tds_ppm(raw_voltage, current_temp):
    # 3.3V 보정 계수 삭제됨! 
    # 단, 물 온도에 따라 TDS 값이 변하므로 온도 보정은 그대로 유지합니다.
    comp_coeff = 1.0 + 0.02 * (current_temp - 25.0)
    comp_v = raw_voltage / comp_coeff
    
    # DFRobot TDS 센서 5V 표준 변환식
    tds_ppm = (133.42 * (comp_v**3) - 255.86 * (comp_v**2) + 857.39 * comp_v) * 0.5
    return max(0.0, tds_ppm)

print("✅ 하드웨어 준비 완료!\n")

# ==========================================
# 🎬 3. 발표 시연용 시나리오 시작
# ==========================================
scenario_data = [
    (2.0, 1.0, 0.0, 0.0, 0, 0),        
    (2.5, 1.5, 22.5, 10.2, 120, 1),    # ⭐ 정상 수질 시연
    (1.5, 5.5, 35.2, 20.5, 300, 1),    # 🚨 오염 수질 시연
    (4.5, 7.8, 23.1, 18.2, 115, 1),    
    (4.0, 2.0, 0.0, 0.0, 0, 2)         # 복귀 및 종료
]

try:
    current_lat, current_lng = 1.0, 1.0 
    print("🏁 발표 시연 모드를 시작합니다. 랩뷰 화면을 확인해 주세요!")

    for i, data in enumerate(scenario_data):
        target_lat, target_lng, sim_temp, sim_turb, sim_tds, status = data
        
        # [이동 단계] 
        print(f"\n🚤 [{target_lat}, {target_lng}] 위치로 이동합니다.")
        set_motor(1850, 1850) 
        
        steps = 40 
        lat_step = (target_lat - current_lat) / steps
        lng_step = (target_lng - current_lng) / steps
        
        for _ in range(steps):
            current_lat += lat_step
            current_lng += lng_step
            packet = f"{current_lat:.4f},{current_lng:.4f},0,0,0,0"
            sock.sendto(packet.encode('utf-8'), (UDP_IP, UDP_PORT))
            time.sleep(0.05) 
            
        # [도착 및 정지]
        set_motor(1750, 1750) 
        
        # --- 측정 로직 분기 ---
        if status == 1:
            if target_lat == 2.5 and target_lng == 1.5:
                print(f"📍 첫 번째 목표 구역 도착! [✅ 정상 수질 측정 시연]")
                
                input("👉 깨끗한 물(정상)에 센서들을 담그고 [Enter] 키를 누르세요...")
                real_temp = read_temp()  
                print(f"   🌡️ 수온 측정: {real_temp:.1f}°C")
                
                if ads:
                    raw_turb = turb_sensor.voltage
                    real_turb = get_turbidity_ntu(raw_turb)
                    print(f"   💧 탁도 측정: {real_turb:.2f} NTU (Raw: {raw_turb:.2f}V)")
                    
                    raw_tds = tds_sensor.voltage
                    real_tds = get_tds_ppm(raw_tds, real_temp)
                    print(f"   🧂 TDS 측정: {real_tds:.2f} ppm (Raw: {raw_tds:.2f}V)")
                else:
                    real_turb, real_tds = sim_turb, sim_tds
                    print("   ⚠️ 센서 미연결: 시뮬레이션 값 전송")
                
                print("📡 정상 데이터 랩뷰로 전송!")
                packet = f"{target_lat:.4f},{target_lng:.4f},{real_temp},{real_turb:.2f},{real_tds:.2f},1"
                sock.sendto(packet.encode('utf-8'), (UDP_IP, UDP_PORT))
                time.sleep(2) 
            
            elif target_lat == 1.5 and target_lng == 5.5:
                print(f"📍 두 번째 목표 구역 도착! [⚠️ 오염 수질 측정 시연]")
                
                input("👉 오염된 물(커피/흙물)에 센서들을 담그고 [Enter] 키를 누르세요...")
                real_temp = read_temp()  
                print(f"   🌡️ 수온 측정: {real_temp:.1f}°C")
                
                if ads:
                    raw_turb = turb_sensor.voltage
                    real_turb = get_turbidity_ntu(raw_turb)
                    print(f"   💧 탁도 측정: {real_turb:.2f} NTU (Raw: {raw_turb:.2f}V)")
                    
                    raw_tds = tds_sensor.voltage
                    real_tds = get_tds_ppm(raw_tds, real_temp)
                    print(f"   🧂 TDS 측정: {real_tds:.2f} ppm (Raw: {raw_tds:.2f}V)")
                else:
                    real_turb, real_tds = sim_turb, sim_tds
                
                print("📡 오염 데이터 랩뷰로 전송! (알람 발생 확인!)")
                packet = f"{target_lat:.4f},{target_lng:.4f},{real_temp},{real_turb:.2f},{real_tds:.2f},1"
                sock.sendto(packet.encode('utf-8'), (UDP_IP, UDP_PORT))
                time.sleep(3) 
            
            else:
                print(f"📍 목표 지점({target_lat}, {target_lng}) 도착. (센서 자동 측정 중...)")
                time.sleep(1) 
                packet = f"{target_lat:.4f},{target_lng:.4f},{sim_temp},{sim_turb},{sim_tds},1"
                sock.sendto(packet.encode('utf-8'), (UDP_IP, UDP_PORT))
                time.sleep(1.5) 
            
        elif status == 2:
            print(f"\n🏁 최종 복귀 지점({target_lat}, {target_lng})에 도착했습니다. 탐사를 종료합니다.")
            packet = f"{target_lat:.4f},{target_lng:.4f},0,0,0,2"
            sock.sendto(packet.encode('utf-8'), (UDP_IP, UDP_PORT))
            break 

except KeyboardInterrupt:
    print("\n🛑 테스트 강제 종료됨.")
    set_motor(1750, 1750)
