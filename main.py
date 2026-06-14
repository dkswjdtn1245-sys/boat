import time
import board
import busio
import serial
import os
import glob

# 1. 필수 라이브러리 임포트
import adafruit_bno055                               # 자이로 센서
import adafruit_ads1x15.ads1115 as ADS               # ADC 컨버터 (탁도, TDS)
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_pca9685 import PCA9685                 # 모터 드라이버

print("🚀 시스템 초기화 시작...")

# 2. I2C 통신 초기화 (공통 사용)
i2c = busio.I2C(board.SCL, board.SDA)

# 3. 자이로 센서 (BNO055) 세팅
try:
    bno = adafruit_bno055.BNO055_I2C(i2c)
    print("✅ 자이로 센서(BNO055) 연결 성공")
except Exception as e:
    print("❌ 자이로 센서 연결 실패:", e)

# 4. ADS1115 (탁도 A0, TDS A1) 세팅
try:
    ads = ADS.ADS1115(i2c)
    # A0, A1 핀 명시적 할당 (에러 우회)
    turb_sensor = AnalogIn(ads, 0)  # 탁도 센서 (A0)
    tds_sensor = AnalogIn(ads, 1)   # TDS 센서 (A1)
    print("✅ ADS1115 (탁도/TDS) 연결 성공")
except Exception as e:
    print("❌ ADS1115 연결 실패:", e)

# 5. 레이저 거리 센서 (TF-Luna UART) 세팅
try:
    ser = serial.Serial('/dev/serial0', 115200, timeout=0.1)
    print("✅ 레이저 센서(TF-Luna) 통신 포트 오픈 성공")
except Exception as e:
    print("❌ 레이저 센서 연결 실패:", e)

# 6. 수온 센서 (DS18B20 1-Wire) 세팅
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
base_dir = '/sys/bus/w1/devices/'
try:
    device_folder = glob.glob(base_dir + '28*')[0]
    device_file = device_folder + '/w1_slave'
    print("✅ 수온 센서(DS18B20) 인식 성공")
except IndexError:
    device_file = None
    print("❌ 수온 센서(DS18B20)를 찾을 수 없습니다. (배선/풀업저항 확인)")

# 7. 모터 드라이버 (PCA9685) 세팅
try:
    pca = PCA9685(i2c)
    pca.frequency = 50 # ESC 제어를 위한 50Hz 세팅
    print("✅ 모터 드라이버 연결 성공")
except Exception as e:
    print("❌ 모터 드라이버 연결 실패:", e)

def set_motor(ch13_pwm, ch15_pwm):
    """주어진 PWM(us) 값으로 모터를 제어하는 함수"""
    if 'pca' not in globals(): return
    duty_13 = int((ch13_pwm / 20000) * 65535)
    duty_15 = int((ch15_pwm / 20000) * 65535)
    pca.channels[13].duty_cycle = duty_13
    pca.channels[15].duty_cycle = duty_15

# [중요] ESC 초기화 및 중립 신호(1750) 전송
print("⏳ ESC 모터 초기화 진행 중... (삐-빅 소리가 날 때까지 3초 대기)")
set_motor(1750, 1750)
time.sleep(3)
print("✅ 모터 초기화 완료!")

# --- 데이터 읽기 보조 함수들 ---
def read_tfluna():
    if 'ser' not in globals() or not ser.is_open: return -1
    # 🔥 레이저 센서 딜레이 해결의 핵심: 읽기 전 버퍼 비우기
    ser.reset_input_buffer()
    timeout = time.time() + 0.5
    while time.time() < timeout:
        if ser.in_waiting >= 9:
            if ser.read(1) == b'Y' and ser.read(1) == b'Y':
                data = ser.read(7)
                return data[0] + (data[1] << 8)
    return -1

def read_temp():
    if device_file is None: return -1
    try:
        with open(device_file, 'r') as f:
            lines = f.readlines()
        if lines[0].strip()[-3:] == 'YES':
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                return float(lines[1][equals_pos+2:]) / 1000.0
    except:
        pass
    return -1

# --- 테스트 사이클 제어 함수 ---
def run_state_and_read_sensors(state_name, pwm_val, duration):
    """지정된 시간 동안 모터를 돌리면서 센서값을 개별적으로 실시간 출력"""
    print(f"\n▶▶ [모터 상태: {state_name} | PWM: {pwm_val}us] ◀◀")
    set_motor(pwm_val, pwm_val)
    
    start_time = time.time()
    while time.time() - start_time < duration:
        # 1. 수온 센서 독립 읽기
        temp = read_temp()
            
        # 2. 탁도 & TDS 센서 독립 읽기
        try:
            turb_v = turb_sensor.voltage if 'turb_sensor' in globals() else 0.0
            tds_v = tds_sensor.voltage if 'tds_sensor' in globals() else 0.0
        except:
            turb_v, tds_v = 0.0, 0.0
            
        # 3. 레이저 센서 독립 읽기
        dist = read_tfluna()
            
        # 4. 자이로 센서 독립 읽기
        heading = 0.0
        try:
            if 'bno' in globals():
                euler = bno.euler
                if euler and euler[0] is not None:
                    heading = euler[0]
        except:
            pass
        
        # 실시간 데이터 출력
        print(f"🌡️수온: {temp:.1f}°C | 💧탁도: {turb_v:.2f}V | 🧂TDS: {tds_v:.2f}V | 📏거리: {dist}cm | 🧭방향: {heading}")
        time.sleep(0.5)

# 8. 메인 테스트 무한 루프
try:
    print("\n🚀 본격적인 통합 테스트 사이클을 시작합니다! (종료하려면 Ctrl+C)")
    while True:
        run_state_and_read_sensors("정지 대기", 1750, 3)
        run_state_and_read_sensors("앞으로 전진", 1850, 3)  # 🔥 수정 완료: 1850us 반영
        run_state_and_read_sensors("모터 멈춤", 1750, 3)
        run_state_and_read_sensors("뒤로 후진", 1650, 3)  # 🔥 수정 완료: 1650us 반영

except KeyboardInterrupt:
    print("\n🛑 테스트 강제 종료됨. 모터를 중립(정지)으로 복귀시킵니다.")
    set_motor(1750, 1750)
    time.sleep(1)
    print("시스템 안전 종료 완료.")
