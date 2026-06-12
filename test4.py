import time
import board
import adafruit_bmp280

# I2C 통신 초기화
i2c = board.I2C()

# 🚨 중요: i2cdetect에서 76이 나왔으므로 주소를 0x76으로 명시해 줍니다.
# (기본 라이브러리 설정값은 0x77이라서 안 적어주면 에러가 날 수 있어!)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)

# 고도 계산을 위한 현재 지역의 해면기압 설정 (기본 표준대기압: 1013.25 hPa)
# 더 정확한 고도를 원하면 오늘 날씨 기상청 해면기압을 넣으면 돼.
bmp280.sea_level_pressure = 1013.25

print("=" * 60)
print("  BMP280 기압/온도 센서 실시간 데이터 테스트 시작")
print("  (종료하려면 Ctrl + C를 누르세요)")
print("=" * 60)

try:
    while True:
        # 데이터 읽기
        temperature = bmp280.temperature  # 섭씨 온도
        pressure = bmp280.pressure        # 기압 (hPa)
        altitude = bmp280.altitude        # 계산된 고도 (m)
        
        print(f"🌡️  온도(Temperature): {temperature:.2f} °C")
        print(f"🎈 기압(Pressure): {pressure:.2f} hPa")
        print(f"⛰️  대략적 고도(Altitude): {altitude:.2f} m")
        print("-" * 60)
        
        time.sleep(1)

except KeyboardInterrupt:
    print("\n👋 BMP280 센서 테스트를 안전하게 종료합니다.")
