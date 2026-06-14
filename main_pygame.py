import time
import board
import busio
import serial
import os
import glob
import socket

# ==========================================
# 📡 1. 무선 통신 세팅 (Pygame 시뮬레이터 전용)
# ==========================================
UDP_IP = "10.242.92.169"  # 조장님 노트북 IP
UDP_PORT = 5005           # 🌟 파이게임이 귀를 열고 있는 포트 번호! (5005)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("🚀 파이게임 디지털 트윈 연동 시스템 초기화 시작...")

# ==========================================
# 🛠️ 2. 하드웨어 센서 및 모터 초기화 (기존과 동일)
# ==========================================
i2c = busio.I2C(board.SCL, board.SDA)

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
print("✅ 하드웨어 준비 완료!\n")

# 수온 센서 세팅
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
base_dir = '/sys/bus/w1/devices/'
try:
    device_file = glob.glob(base_dir + '28*')[0] + '/w1_slave'
except:
    device_file = None

def read_temp():
    if device_file is None: return 21.5 # 에러 시 기본값
    try:
        with open(device_file, 'r') as f: lines = f.readlines()
        if lines[0].strip()[-3:] == 'YES':
            idx = lines[1].find('t=')
            if idx != -1: return float(lines[1][idx+2:]) / 1000.0
    except: pass
    return 21.5

# 🌟 전방 장애물 레이저 센서 (TF-Luna UART) 세팅
try:
    ser_laser = serial.Serial("/dev/serial0", 115200, timeout=0.1)
    print("✅ TF-Luna 레이저 센서 연결 성공")
except:
    ser_laser = None
    print("❌ TF-Luna 레이저 센서 연결 실패")

def read_laser():
    """TF-Luna 센서의 버퍼를 비우고 최신 거리(cm) 데이터를 빠르게 읽어옵니다."""
    if ser_laser is None: return 500 # 연결 안 됐을 땐 안전거리(500) 반환
    ser_laser.reset_input_buffer() # 지연 방지를 위해 쓰레기 데이터 폐기
    try:
        while True:
            if ser_laser.in_waiting >= 9:
                if ser_laser.read(1) == b'\x59' and ser_laser.read(1) == b'\x59':
                    raw_data = ser_laser.read(7)
                    dist = raw_data[0] + raw_data[1] * 256
                    return dist
    except: pass
    return 500


# ==========================================
# 🎬 3. Pygame 전용 실시간 데이터 쏘기 (0.1초마다)
# ==========================================
# 💡 핵심: Pygame은 스스로 상태를 판단(회피, 빙글빙글)하므로, 
# 라즈베리파이는 "현재 센서 값"만 기관총처럼 계속 쏴주면 됩니다!

print(f"\n🏁 [{UDP_IP}:{UDP_PORT}]로 센서 데이터 전송을 시작합니다!")
print("👉 노트북에서 Pygame 코드를 켜시고, 레이저 센서에 손을 대보세요!")

try:
    while True:
        # 1. 실제 센서 읽기
        real_temp = round(read_temp(), 1)
        real_laser = read_laser()
        
        # 💡 탁도와 TDS는 현재 수동 측정 시나리오이므로, Pygame 시연의
        # 극적인 효과를 위해 일단 기본값을 넣어줍니다. (오염 구역은 Pygame이 알아서 가짜로 띄움)
        turb_val = 1.2
        tds_val = 120
        heading_val = 180.0

        # 2. Pygame이 좋아하는 포맷으로 패킷 조립
        # "수온,탁도,TDS,방향,레이저거리"
        packet = f"{real_temp},{turb_val},{tds_val},{heading_val},{real_laser}"
        
        # 3. 노트북(Pygame)으로 0.1초마다 계속 쏘기!
        sock.sendto(packet.encode('utf-8'), (UDP_IP, UDP_PORT))
        
        print(f"[전송중] 온도:{real_temp}℃ | 거리:{real_laser}cm -> {packet}")
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n🛑 테스트 강제 종료. 모터를 정지합니다.")
    set_motor(1750, 1750)
