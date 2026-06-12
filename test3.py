import time
import board
import adafruit_bno055

# I2C 통신 초기화 (라즈베리파이의 SCL, SDA 핀 자동 지정)
i2c = board.I2C()
sensor = adafruit_bno055.BNO055_I2C(i2c)

print("=" * 60)
print("  BNO055 IMU 자이로 센서 실시간 데이터 테스트 시작")
print("  (종료하려면 Ctrl + C를 누르세요)")
print("=" * 60)

try:
    while True:
        # 오일러 각도 데이터 읽기 (정상적으로 읽히지 않으면 None 반환)
        euler = sensor.euler
        
        # 캘리브레이션 상태 읽기 (시스템, 자이로, 가속도, 지자기 순서)
        # 0(미흡) ~ 3(완벽) 단계로 표시됨
        cal_sys, cal_gyro, cal_accel, cal_mag = sensor.calibration_status

        if euler and euler[0] is not None:
            heading = euler[0] # 0도(북) ~ 360도 회전각
            roll = euler[1]    # 좌우 회전/기울임
            pitch = euler[2]   # 앞뒤 회전/기울임
            
            print(f"🧭 방향(Heading): {heading:>6.1f}° | 롤(Roll): {roll:>6.1f}° | 피치(Pitch): {pitch:>6.1f}°")
            print(f"⚙️  캘리브레이션 상태 -> SYS: {cal_sys} | GYRO: {cal_gyro} | ACCEL: {cal_accel} | MAG: {cal_mag}")
            print("-" * 60)
        else:
            print("⚠️ 센서 데이터를 읽어오는 중 오류가 발생했습니다. 결선을 확인하세요.")
            
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n👋 BNO055 센서 테스트를 안전하게 종료합니다.")
