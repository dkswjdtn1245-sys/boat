import time
import board
import busio
from adafruit_pca9685 import PCA9685

# 1. I2C 버스 및 PCA9685 모듈 초기화
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50  # 50Hz 고정

# 15번 채널 사용
motor = pca.channels[15]

# 📊 조장님이 실전 스캔으로 찾아낸 마법의 기준값 세팅
NEUTRAL_PULSE = 1750  # 1740~1780 구간의 완벽한 센터 (정지 및 아밍용)
LOW_SPEED_CW  = 1700  # 중립(1750)에서 아래로 내려서 오른쪽 회전 (약하게)
LOW_SPEED_CCW = 1800  # 중립(1750)에서 위로 올리서 왼쪽 회전 (약하게)

def set_motor_pulse(us):
    # us 펄스 신호를 PCA9685가 인식하는 16비트 duty_cycle로 변환
    duty_cycle = int((us / 20000.0) * 65535)
    motor.duty_cycle = duty_cycle

try:
    print("=========================================")
    print(f"🎯 1750us 기준 맞춤형 구동 테스트 시작")
    print("=========================================")
    
    print(f"📢 [1단계] ESC 아밍(Arming) 시도 ➡️ 신호: {NEUTRAL_PULSE}us")
    print("4초간 대기합니다. 잠금 해제음(비프음)을 확인하세요.")
    for i in range(4):
        set_motor_pulse(NEUTRAL_PULSE)
        time.sleep(1)
        
    print("✅ 아밍 완료! 잠금이 정상적으로 해제되었습니다.")
    time.sleep(1)

    # ----------오른쪽 회전 테스트 ----------
    print(f"\n🔄 [2단계] 오른쪽 회전 (CW) 구동 ➡️ 신호: {LOW_SPEED_CW}us")
    print("안전을 위해 약한 속도로 3초간 회전합니다.")
    set_motor_pulse(LOW_SPEED_CW)
    time.sleep(3)

    print(f"⏹️ [3단계] 중간 브레이크 ➡️ 신호: {NEUTRAL_PULSE}us (2초간 정지)")
    set_motor_pulse(NEUTRAL_PULSE)
    time.sleep(2)

    # ---------- 왼쪽 회전 테스트 ----------
    print(f"\n🔄 [4단계] 왼쪽 회전 (CCW) 구동 ➡️ 신호: {LOW_SPEED_CCW}us")
    print("반대 방향으로 약한 속도로 3초간 회전합니다.")
    set_motor_pulse(LOW_SPEED_CCW)
    time.sleep(3)

    print(f"\n⏹️ [5단계] 테스트 종료, 모터 정지 신호 송신")
    set_motor_pulse(NEUTRAL_PULSE)
    time.sleep(1)

except KeyboardInterrupt:
    print("\n⚠️ 사용자가 Ctrl+C를 눌러 안전 종료를 발동함")

finally:
    # 🚨 최우선 안전 수칙: 코드가 끝나면 무조건 전원을 물리적으로 차단(0)해야 안전함
    set_motor_pulse(NEUTRAL_PULSE)
    time.sleep(0.3)
    motor.duty_cycle = 0
    pca.deinit()
    print("🔒 모터 제어 신호가 안전하게 완전 차단되었습니다. 종료합니다.")
