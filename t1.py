import time
import board
import busio
import serial
import adafruit_bno055
from adafruit_pca9685 import PCA9685

# ==========================================
# 1. 하드웨어 및 통신 초기화
# ==========================================
i2c = busio.I2C(board.SCL, board.SDA)

# BNO055 자이로 센서
try:
    bno = adafruit_bno055.BNO055_I2C(i2c)
    print("✅ 자이로 센서 (I2C 0x28) 연결 성공!")
except Exception as e:
    bno = None
    print(f"⚠️ 자이로 센서 연결 실패: {e}")

# PCA9685 모터 드라이버
try:
    pca = PCA9685(i2c)
    pca.frequency = 50 # ESC 표준 주파수 50Hz
    print("✅ 모터 드라이버 (I2C 0x40) 연결 성공!")
except Exception as e:
    pca = None
    print(f"⚠️ 모터 드라이버 연결 실패: {e}")

def set_motor_pwm(channel, pulse_us):
    """ 마이크로초(us) 단위로 PWM 신호를 쏴주는 함수 """
    if pca is None:
        return
    duty = int((pulse_us / 20000.0) * 65535)
    pca.channels[channel].duty_cycle = duty

# USB GPS 센서 (TEL0138)
try:
    gps_serial = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=0.1)
    print("✅ GPS 포트 (/dev/ttyUSB0) 오픈 성공!")
except Exception as e:
    gps_serial = None
    print(f"⚠️ GPS 포트 열기 실패: {e} (sudo 권한을 확인하거나 포트 확인)")

# TF-Luna 레이저 거리 센서 (UART)
try:
    tfluna_serial = serial.Serial('/dev/serial0', baudrate=115200, timeout=0.1)
    print("✅ TF-Luna 포트 (/dev/serial0) 오픈 성공!")
except Exception as e:
    tfluna_serial = None
    print(f"⚠️ TF-Luna 포트 열기 실패: {e} (sudo 권한 확인 필요)")

# ==========================================
# 2. ESC 모터 초기화 (Arming) - 정지 기준 1750us 적용
# ==========================================
# 조장님 피드백 반영: 이 모터는 1750us가 들어와야 락이 풀립니다.
STOP_PWM = 1750 

if pca:
    print(f"\n🚀 ESC 모터 초기화 진행 중... 중립 신호({STOP_PWM}us) 인가")
    set_motor_pwm(13, STOP_PWM) 
    set_motor_pwm(15, STOP_PWM)
    print("⏳ ESC에서 '띠리릭-' 시동 확인음이 날 때까지 4초간 대기합니다...")
    time.sleep(4) 
    print("✅ 모터 초기화 완료! 테스트 루프를 시작합니다.\n")

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
        heading = "측정불가"
        if bno:
            try:
                heading = f"{bno.euler[0]:.1f}°" if bno.euler and bno.euler[0] is not None else "계산중"
            except:
                heading = "통신오류"

        # 2. TF-Luna 거리 데이터
        distance = "수신대기"
        if tfluna_serial and tfluna_serial.in_waiting >= 9:
            try:
                tfluna_serial.reset_input_buffer()
                if tfluna_serial.read(1) == b'\x59' and tfluna_serial.read(1) == b'\x59':
                    dist_bytes = tfluna_serial.read(2)
                    dist_cm = dist_bytes[0] + dist_bytes[1] * 256
                    distance = f"{dist_cm}cm"
                    tfluna_serial.read(5)
            except:
                distance = "에러"
                
        # 3. GPS 데이터 (실내 상태 예외 처리)
        gps_data = "실내(위성 안잡힘)"
        if gps_serial and gps_serial.in_waiting > 0:
            try:
                line = gps_serial.readline().decode('ascii', errors='replace').strip()
                if line.startswith("$G"):
                    gps_data = "데이터 신호 수신 중"
            except:
                pass

        # --- [B] 모터 동작 사이클 제어 (정지 1750, 전진 1790이상, 후진 1730이하) ---
        cycle = int(elapsed) % 12
        
        if cycle < 3:
            motor_state = "전진 가동 (1810us)"
            set_motor_pwm(13, 1810) # 1790 이상 작동 조건 만족
            set_motor_pwm(15, 1810)
        elif cycle < 6:
            motor_state = "안전 정지 (1750us)"
            set_motor_pwm(13, STOP_PWM) # 정지 기준점 1750
            set_motor_pwm(15, STOP_PWM)
        elif cycle < 9:
            motor_state = "후진 가동 (1700us)"
            set_motor_pwm(13, 1700) # 1730 이하 작동 조건 만족
            set_motor_pwm(15, 1700)
        else:
            motor_state = "안전 정지 (1750us)"
            set_motor_pwm(13, STOP_PWM)
            set_motor_pwm(15, STOP_PWM)

        # --- [C] 터미널 통합 출력 ---
        print(f"[{motor_state}] 자이로방향: {heading} | 레이저거리: {distance:>5} | GPS상태: {gps_data}")
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n🛑 테스트 강제 종료! 모터를 정지 기준점(1750us)으로 복귀시킵니다.")
    set_motor_pwm(13, STOP_PWM)
    set_motor_pwm(15, STOP_PWM)
