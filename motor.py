import sys
import tty
import termios
import time
import board
import busio
from adafruit_pca9685 import PCA9685

# 💡 SSH 터미널(Termius)에서 Enter 없이 키 입력을 바로 받기 위한 함수
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

# 1. PCA9685 모듈 초기화
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50  # 50Hz 고정

# 15번 채널 사용
motor = pca.channels[15]

# 펄스 값을 duty_cycle로 변환하는 함수
def set_motor_pulse(us):
    duty_cycle = int((us / 20000.0) * 65535)
    motor.duty_cycle = duty_cycle

# 초기 값 세팅
current_pulse = 1500

print("🟢 [시작] 모터 제어 회로 정상 인식됨.")
print("📢 초기 정지 신호(1500us)를 송신합니다...")
set_motor_pulse(current_pulse)
time.sleep(1)

print("\n=========================================")
print("🎮 실시간 모터 PWM 매칭 테스트 모드")
print("=========================================")
print(" [w] : 펄스 값 +10us (가속)")
print(" [s] : 펄스 값 1500us로 리셋 (긴급 정지)")
print(" [q] : 프로그램 안전 종료 및 신호 차단")
print("=========================================")
print("⚠️ 주의: 모터가 갑자기 돌 수 있으니 꽉 잡으세요!")

try:
    while True:
        # \r을 이용해 한 줄에 실시간으로 현재 펄스 표시
        print(f"\r▶️ 현재 출력 펄스: {current_pulse} us ", end="", flush=True)
        
        key = getch()
        
        # w 누르면 10씩 증가 (최대 2000)
        if key == 'w' or key == 'W':
            current_pulse += 10
            if current_pulse > 2000:
                current_pulse = 2000
                
        # s 누르면 정지(1500)로 리셋
        elif key == 's' or key == 'S':
            current_pulse = 1500
            print("\n🛑 [🛑 긴급 정지] 1500us 리셋 완료.")
            
        # q 누르면 루프 탈출
        elif key == 'q' or key == 'Q':
            print("\n\n👋 프로그램을 종료합니다.")
            break
            
        # ESC에 실시간으로 계산된 PWM 신호 전송
        set_motor_pulse(current_pulse)

except KeyboardInterrupt:
    print("\n\n⚠️ Ctrl+C 강제 종료 감지")

finally:
    # 🚨 종료 시 무조건 안전하게 서보 신호를 0으로 날려 전원 완전 차단
    set_motor_pulse(1500)
    time.sleep(0.3)
    motor.duty_cycle = 0
    pca.deinit()
    print("🔒 모터 신호가 안전하게 차단되었습니다.")
