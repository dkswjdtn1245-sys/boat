import time
import board
import busio
import serial
import adafruit_bno055
from adafruit_pca9685 import PCA9685

# ==========================================
# 1. 하드웨어 및 통신 초기화
# ==========================================
# I2C 통신 버스 열기 (자이로 및 모터 드라이버 공용)
i2c = busio.I2C(board.SCL, board.SDA)

# BNO055 자이로 센서
try:
    bno = adafruit_bno055.BNO055_I2C(i2c)
except Exception as e:
    print(f"⚠️ 자이로 센서 연결 오류: {e}")

# PCA9685 모터 드라이버
pca = PCA9685(i2c)
pca.frequency = 50 # ESC 표준 주파수 (50Hz = 20ms 주기)

def set_motor_pwm(channel, pulse_us):
    """ 마이크로초(us) 단위로 PWM 신호를 쏴주는 함수 """
    # 50Hz(20,000us) 기준으로 16비트(65535) 듀티 사이클 계산
    duty = int((pulse_us / 20000.0) * 65535)
    pca.channels[channel].duty_cycle = duty

# USB GPS 센서 (TEL0138)
try:
    gps_serial = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=0.1)
except:
    gps_serial = None
    print("⚠️ GPS 포트(/dev/ttyUSB0)를 열 수 없습니다. 포트 번호를 확인하세요.")

# TF-Luna 레이저 거리 센서 (UART)
try:
    tfluna_serial = serial.Serial('/dev/serial0', baudrate=115200, timeout=0.1)
except:
    tfluna_serial = None
    print("⚠️ TF-Luna 포트(/dev/serial0)를 열 수 없습니다.")

# ==========================================
# 2. ESC 모터 초기화 (Arming) - 매우 중요!
# ==========================================
print("\n🚀 ESC 모터 초기화 진행 중... (삐-빅 소리가 날 때까지 대기)")
set_motor_pwm(13, 1500) # 13번 채널 중립
set_motor_pwm(15, 1500) # 15번 채널 중립
time.sleep(3) # ESC가 중립 신호를 인식하고 시동을 걸 시간을 줍니다.
print("✅ 모터 초기화 완료! 테스트를 시작합니다.\n")

# ==========================================
# 3. 메인 무한 루프 (센서 읽기 + 모터 제어)
# ==========================================
start_time = time.time()

try:
    while True:
        current_time = time.time()
        elapsed = current_time - start_time
        
        # --- [A] 센서 데이터 수집 ---
        
        # 1. 자이로(Heading) 데이터
        try:
            heading = f"{bno.euler[0]:.1f}°" if bno.euler and bno.euler[0] is not None else "측정 중"
        except:
            heading = "오류"

        # 2. TF-Luna 거리 데이터 (밀린 버퍼 털어내기 적용)
        distance = "대기중"
        if tfluna_serial and tfluna_serial.in_waiting >= 9:
            tfluna_serial.reset_input_buffer()
            if tfluna_serial.read(1) == b'\x59' and tfluna_serial.read(1) == b'\x59':
                dist_bytes = tfluna_serial.read(2)
                dist_cm = dist_bytes[0] + dist_bytes[1] * 256
                distance = f"{dist_cm}cm"
                tfluna_serial.read(5) # 나머지 더미 바이트 소진
                
        # 3. GPS 데이터 (가장 최신 NMEA 문장 읽기)
        gps_data = "수신 대기..."
        if gps_serial and gps_serial.in_waiting > 0:
            line = gps_serial.readline().decode('ascii', errors='replace').strip()
            if line.startswith("$GNRMC") or line.startswith("$GNGGA"):
                gps_data = "수신 성공 (NMEA 데이터 들어옴)"

        # --- [B] 모터 동작 사이클 제어 ---
        # 12초 주기로 동작 상태를 바꿉니다. (조장님 지정: 1790 이상, 1730 이하)
        cycle = int(elapsed) % 12
        
        if cycle < 3:
            motor_state = "전진 (1800us)"
            set_motor_pwm(13, 1800) # 1790 이상이므로 1800 넉넉하게 인가
            set_motor_pwm(15, 1800)
        elif cycle < 6:
            motor_state = "정지 (1500us)"
            set_motor_pwm(13, 1500)
            set_motor_pwm(15, 1500)
        elif cycle < 9:
            motor_state = "후진 (1700us)"
            set_motor_pwm(13, 1700) # 1730 이하이므로 1700 인가
            set_motor_pwm(15, 1700)
        else:
            motor_state = "정지 (1500us)"
            set_motor_pwm(13, 1500)
            set_motor_pwm(15, 1500)

        # --- [C] 터미널 통합 출력 ---
        print(f"[{motor_state}] 자이로방향: {heading} | 전방거리: {distance:>5} | GPS: {gps_data}")
        
        time.sleep(0.1) # 화면이 너무 빨리 올라가는 것을 방지

except KeyboardInterrupt:
    # Ctrl+C 누를 시 가장 중요한 안전 종료 로직
    print("\n🛑 테스트 강제 종료! 모터를 중립(1500us)으로 안전하게 정지합니다.")
    set_motor_pwm(13, 1500)
    set_motor_pwm(15, 1500)
