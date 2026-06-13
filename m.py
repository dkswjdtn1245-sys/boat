import time
import board
import busio
from adafruit_pca9685 import PCA9685

# 1. I2C 버스 및 PCA9685 모듈 초기화
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50  # 50Hz 고정

# 2. 좌우 모터 채널 할당 (13번, 15번)
motor_left = pca.channels[13]   # 좌측 모터
motor_right = pca.channels[15]  # 우측 모터

# 📊 조장님이 찾아낸 마법의 센터값
NEUTRAL_PULSE = 1750  # 정지 및 아밍용 기준점

# 💡 두 모터에 동시에us 펄스 신호를 쏴주는 함수
def set_dual_motors(left_us, right_us):
    left_duty = int((left_us / 20000.0) * 65535)
    right_duty = int((right_us / 20000.0) * 65535)
    motor_left.duty_cycle = left_duty
    motor_right.duty_cycle = right_duty

try:
    print("=========================================")
    print("🚀 듀얼 모터(CH 13, CH 15) 동시 제어 테스트")
    print("=========================================")
    
    print(f"📢 [1단계] 양쪽 ESC 동시 아밍(Arming) 시작... (신호: {NEUTRAL_PULSE}us)")
    print("4초간 대기합니다. 양쪽 변속기에서 잠금 해제음이 동시에 나야 합니다.")
    for i in range(4):
        set_dual_motors(NEUTRAL_PULSE, NEUTRAL_PULSE)
        time.sleep(1)
        
    print("✅ 양쪽 모터 잠금 해제 완료! 2초 뒤 구동 시작합니다.")
    time.sleep(2)

    # 🛫 [테스트 1] 전진 기동
    # 조장님의 모터 특성상 센터(1750) 기준으로 둘 다 수치를 올리거나, 
    # 둘 다 수치를 내렸을 때 프로펠러 날개 방향과 맞물려 물을 '뒤로' 밀어내게 됩니다.
    # 여기서는 둘 다 1850us 신호를 주어 양방향 토크를 상쇄하며 전진하는지 테스트합니다.
    print("\n▶️ [2단계] 양쪽 모터 동시 전진 기동! (신호: 1850us / 1850us)")
    print("⚠️ 모터 축 2개가 서로 반대 방향으로 돌면서 바람은 둘 다 뒤로 부는지 확인하세요!")
    set_dual_motors(1850, 1850)
    time.sleep(3)

    # ⏹️ [브레이크] 중간 정지
    print(f"\n⏹️ [3단계] 중간 정지 ➡️ {NEUTRAL_PULSE}us 송신 (2초 대기)")
    set_dual_motors(NEUTRAL_PULSE, NEUTRAL_PULSE)
    time.sleep(2)

    # 🛬 [테스트 2] 후진 기동
    # 값을 반대 대역인 1650us로 내려서 물을 '앞으로' 뿜어내는지 확인합니다.
    print("\n◀️ [4단계] 양쪽 모터 동시 후진 기동! (신호: 1650us / 1650us)")
    set_dual_motors(1650, 1650)
    time.sleep(3)

    print("\n⏹️ [5단계] 테스트 완료! 모터 정지 신호 송신")
    set_dual_motors(NEUTRAL_PULSE, NEUTRAL_PULSE)
    time.sleep(1)

except KeyboardInterrupt:
    print("\n⚠️ 사용자가 Ctrl+C를 눌러 긴급 정지 발동!")

finally:
    # 🚨 안전 최우선: 프로그램 종료 시 양쪽 채널의 신호를 완전히 끊어 급발진 방지
    set_dual_motors(NEUTRAL_PULSE, NEUTRAL_PULSE)
    time.sleep(0.3)
    motor_left.duty_cycle = 0
    motor_right.duty_cycle = 0
    pca.deinit()
    print("🔒 좌우 구동계 전원이 완전히 안전하게 차단되었습니다.")
