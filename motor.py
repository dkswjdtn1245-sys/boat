import sys
import tty
import termios
import time
import board
import busio
from adafruit_pca9685 import PCA9685

# SSH 터미널 키 입력 함수
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

# PCA9685 초기화
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50

motor = pca.channels[15]

def set_motor_pulse(us):
    duty_cycle = int((us / 20000.0) * 65535)
    motor.duty_cycle = duty_cycle

# 💡 탐색 시작 값을 1500으로 두고 위아래로 다 가봅니다.
current_pulse = 1500
set_motor_pulse(current_pulse)

print("\n=========================================")
print("🔍 1000us ~ 2100us 전 대역 풀 스캔 모드")
print("=========================================")
print(" [w] : 펄스 값 +10us (올리기)")
print(" [s] : 펄스 값 -10us (내리기)")
print(" [space] : 즉시 1500us로 리셋")
print(" [q] : 안전 종료 (신호 차단)")
print("=========================================")
print("⚠️ 모터 몸통을 꼭 잡고 테스트하세요!")

try:
    while True:
        print(f"\r▶️ 현재 출력 펄스: {current_pulse} us  ", end="", flush=True)
        
        key = getch()
        
        if key == 'w' or key == 'W':
            current_pulse += 10
            if current_pulse > 2100: current_pulse = 2100
        elif key == 's' or key == 'S':
            current_pulse -= 10
            if current_pulse < 1000: current_pulse = 1000
        elif key == ' ':  # 스페이스바
            current_pulse = 1500
            print("\n⏹️ 1500us 리셋")
        elif key == 'q' or key == 'Q':
            print("\n\n👋 스캔을 종료합니다.")
            break
            
        set_motor_pulse(current_pulse)

except KeyboardInterrupt:
    print("\n\n⚠️ 강제 종료 감지")

finally:
    # 안전하게 신호 완전 차단
    motor.duty_cycle = 0
    pca.deinit()
    print("🔒 모터 전원 안전 차단 완료.")
