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
UDP_IP = "10.242.92.169"  # 👉 알려주신 IP로 완벽 세팅!
UDP_PORT = 8080
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("🚀 관제 시스템 및 하드웨어 초기화 시작...")

# ==========================================
# 🛠️ 2. 하드웨어 센서 및 모터 초기화 (기존 조원 코드)
# ==========================================
i2c = busio.I2C(board.SCL, board.SDA)

try:
    from adafruit_pca9685 import PCA9685
    pca = PCA9685(i2c)
    pca.frequency = 50
    print("✅ 모터 드라이버 연결 성공")
except: print("❌ 모터 드라이버 연결 실패")

def set_motor(ch13_pwm, ch15_pwm):
    if 'pca' not in globals(): return
    pca.channels[13].duty_cycle = int((ch13_pwm / 20000) * 65535)
    pca.channels[15].duty_cycle = int((ch15_pwm / 20000) * 65535)

print("⏳ 모터 초기화 진행 중... (삐-빅 소리 대기)")
set_motor(1750, 1750)
time.sleep(3)
print("✅ 하드웨어 준비 완료!\n")

# ==========================================
# 🎬 3. 발표 시연용 시나리오 (입력해주신 테스트 데이터 적용)
# ==========================================
# (목표위도, 목표경도, 수온, 탁도, TDS, 상태코드)
scenario_data = [
    (2.0, 1.0, 0.0, 0.0, 0, 0),        # 1. 단순 출발 이동
    (2.5, 1.5, 22.5, 10.2, 120, 1),    # 2. 측정 (정상)
    (1.5, 5.5, 35.2, 20.5, 300, 1),    # 3. 측정 (⚠️수온, TDS 오염!)
    (4.5, 7.8, 23.1, 18.2, 115, 1),    # 4. 측정 (정상)
    (8.3, 8.0, 23.8, 12.1, 130, 1),    # 5. 측정 (정상)
    (7.5, 5.0, 23.8, 50.1, 130, 1),    # 6. 측정 (⚠️탁도 오염!)
    (8.5, 1.5, 22.3, 10.5, 110, 1),    # 7. 측정 (정상)
    (6.0, 2.5, 24.5, 15.2, 120, 1),    # 8. 측정 (정상)
    (4.0, 2.0, 0.0, 0.0, 0, 2)         # 9. 복귀 및 종료
]

try:
    current_lat, current_lng = 1.0, 1.0 # 보트의 최초 시작 위치

    print("🏁 발표 시연 모드를 시작합니다. 랩뷰 화면을 확인해 주세요!")

    for i, data in enumerate(scenario_data):
        target_lat, target_lng, sim_temp, sim_turb, sim_tds, status = data
        
        # ----------------------------------------------------
        # [단계 1: 이동] 모터를 돌리며 가상 GPS 좌표 부드럽게 전송
        # ----------------------------------------------------
        print(f"\n🚤 [{target_lat}, {target_lng}] 위치로 이동합니다. (실제 모터 전진 중!)")
        set_motor(1850, 1850) # 실제 모터 전진 구동!
        
        steps = 40 # 40조각으로 잘게 쪼개어 부드럽게 이동
        lat_step = (target_lat - current_lat) / steps
        lng_step = (target_lng - current_lng) / steps
        
        for _ in range(steps):
            current_lat += lat_step
            current_lng += lng_step
            
            # ⭐ 여기에 상태 '0'이 들어있습니다! (맨 끝 숫자)
            packet = f"{current_lat:.4f},{current_lng:.4f},0,0,0,0"
            sock.sendto(packet.encode('utf-8'), (UDP_IP, UDP_PORT))
            time.sleep(0.05) # 부드러운 애니메이션을 위한 짧은 대기
            
        # ----------------------------------------------------
        # [단계 2: 정지 및 상태 1, 2 발사] 목표 지점 도착
        # ----------------------------------------------------
        set_motor(1750, 1750) # 일단 도착했으니 모터 정지!
        
        if status == 1:
            print(f"📍 목표 지점 도착! 측정 준비. (모터 정지!)")
            
            # 발표 퍼포먼스를 위한 대기 (엔터키를 눌러야 측정 데이터 전송)
            input("👉 퍼포먼스 준비가 되면 [Enter] 키를 누르세요...")
            
            # ⭐ 여기에 상태 '1'이 들어있습니다! (테스트 데이터 쏘기)
            packet = f"{target_lat:.4f},{target_lng:.4f},{sim_temp},{sim_turb},{sim_tds},1"
            sock.sendto(packet.encode('utf-8'), (UDP_IP, UDP_PORT))
            print(f"✅ 상태 1 전송! (측정 완료, 랩뷰 경고등 확인)")
            time.sleep(2) # 심사위원이 화면 볼 시간 주기
            
        elif status == 2:
            print(f"\n🏁 최종 복귀 지점에 도착했습니다. 시스템을 종료합니다.")
            
            # ⭐ 여기에 상태 '2'가 들어있습니다! 
            packet = f"{target_lat:.4f},{target_lng:.4f},0,0,0,2"
            sock.sendto(packet.encode('utf-8'), (UDP_IP, UDP_PORT))
            break # 반복문 탈출 및 시연 종료

except KeyboardInterrupt:
    print("\n🛑 테스트 강제 종료됨.")
    set_motor(1750, 1750)
