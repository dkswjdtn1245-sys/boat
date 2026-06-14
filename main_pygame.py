import time
import board
import busio
import serial
import socket

# ==========================================
# 📡 1. 무선 통신 세팅 (Pygame 시뮬레이터 전용)
# ==========================================
UDP_IP = "10.242.92.169"  # 조장님 노트북 IP (Pygame이 켜져 있는 컴퓨터)
UDP_PORT = 5005           # Pygame 수신 포트 번호
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print(f"🚀 노트북({UDP_IP}:{UDP_PORT})으로 센서 데이터 송신 준비 완료...")

# ==========================================
# 🛠️ 2. 하드웨어 센서 초기화 (BNO055 & TF-Luna)
# ==========================================
i2c = busio.I2C(board.SCL, board.SDA)

# 🌟 BNO055 자이로 센서 세팅
try:
    import adafruit_bno055
    bno = adafruit_bno055.BNO055_I2C(i2c)
    print("✅ BNO055 자이로 센서 연결 성공")
except Exception as e:
    bno = None
    print(f"❌ BNO055 자이로 센서 연결 실패: {e}")

# 🌟 TF-Luna 레이저 거리 센서 세팅 (UART 방식)
try:
    ser_laser = serial.Serial("/dev/serial0", 115200, timeout=0.1)
    print("✅ TF-Luna 레이저 센서 연결 성공")
except Exception as e:
    ser_laser = None
    print(f"❌ TF-Luna 레이저 센서 연결 실패: {e}")

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
# 🎬 3. Pygame으로 실시간 데이터 쏘기 (0.1초 루프)
# ==========================================
print("\n🏁 [디지털 트윈 연동 모드]를 시작합니다!")
print("👉 노트북에서 Pygame 코드를 켜시고, 보트를 손으로 기울여 보세요!")
print("👉 레이저 센서 앞에 손을 대면 장애물 회피 기동을 합니다!\n")

try:
    while True:
        # 1. 🌟 진짜 BNO055 자이로 데이터 읽기 (Heading, Roll, Pitch)
        if bno:
            # euler 속성은 (Heading, Roll, Pitch) 튜플을 반환합니다.
            euler = bno.euler
            if euler[0] is not None:
                real_heading = round(euler[0], 1)
                real_roll = round(euler[1], 1)
                real_pitch = round(euler[2], 1)
            else:
                real_heading, real_roll, real_pitch = 0.0, 0.0, 0.0
        else:
            # 센서 연결 실패 시 기본값 (시뮬레이터가 에러 나지 않도록)
            real_heading, real_roll, real_pitch = 0.0, 0.0, 0.0

        # 2. 🌟 진짜 TF-Luna 레이저 거리 읽기
        real_laser = read_laser()
        
        # 💡 수온, 탁도, TDS는 이번 시연(자이로/레이저 연동)에서는 핵심이 아니므로 
        # 화면에 에러가 안 뜨게 기본값만 세팅해서 보내줍니다.
        temp_val = 22.5
        turb_val = 1.2
        tds_val = 120

        # 3. Pygame이 기다리는 포맷으로 패킷 조립
        # "온도,탁도,TDS,방위각,레이저거리,롤,피치"
        packet = f"{temp_val},{turb_val},{tds_val},{real_heading},{real_laser},{real_roll},{real_pitch}"
        
        # 4. 노트북(Pygame)으로 0.1초마다 쏘기!
        sock.sendto(packet.encode('utf-8'), (UDP_IP, UDP_PORT))
        
        # 터미너스 화면에 현재 무슨 값을 쏘고 있는지 출력 (디버깅용)
        print(f"[송신중] Heading:{real_heading}° | Roll:{real_roll}° | Pitch:{real_pitch}° | LiDAR:{real_laser}cm")
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n🛑 테스트 강제 종료. 센서 측정을 멈춥니다.")
