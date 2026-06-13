import time
import board
import busio
from adafruit_pca9685 import PCA9685

# 1. I2C 버스 및 PCA9685 모듈 초기화
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50  # ESC 및 서보모터 제어 표준인 50Hz로 설정

# 15번 채널 지정
motor = pca.channels[15]

# 💡 50Hz 대역에서 마이크로초(us) 신호를 12비트 duty_cycle 값으로 변환하는 함수
# 1000us = 역회전 맥스 / 1500us = 정지 및 아밍 / 2000us = 정회전 맥스
def set_motor_pulse(us):
    duty_cycle = int((us / 20000.0) * 65535) # 16비트 변환
    motor.duty_cycle = duty_cycle

try:
    print("📢 [단계 1] ESC 아밍(Arming) 시작...")
    print("스러스터(양방향 ESC)의 정지 신호인 1500us를 3초간 보냅니다.")
    print("이때 ESC에서 '삐리릭~' 하고 잠금 해제 비프음이 나야 합니다.")
    
    for i in range(3):
        set_motor_pulse(1500)  # 1500us = 중립(정지) 신호
        time.sleep(1)
        
    print("✅ 아밍 완료! 구동 준비 완료.")
    time.sleep(1)

    print("🚀 [단계 2] 모터 약 가속 테스트 (2초간 구동)")
    # 안전을 위해 아주 살짝만 올린 1560us 신호를 줍니다. (숫자를 키우면 더 빨라짐)
    set_motor_pulse(1560)  
    time.sleep(2)

    print("🛑 [단계 3] 모터 정지 신호 송신")
    set_motor_pulse(1500)
    time.sleep(1)

except KeyboardInterrupt:
    print("\n⚠️ 사용자가 Ctrl+C를 눌러 강제 종료함")

finally:
    # 🚨 안전 수칙: 프로그램이 끝나면 무조건 모터 신호를 완전히 차단(0)해야 안전해!
    motor.duty_cycle = 0
    pca.deinit()
    print("🔒 안전하게 전원을 차단하고 종료했습니다.")
