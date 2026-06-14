import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# 1. I2C 버스 및 ADS1115 초기화
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# 2. Gain 설정 (5V 환경)
# 최대 6.144V까지 측정 가능한 2/3으로 설정하여 5V 전압을 넉넉하고 안전하게 읽습니다.
ads.gain = 2/3

# 3. 핀 지정 (최신 라이브러리 문법 적용)
# 기존 ADS.P0 대신 AnalogIn(ads, 0)을 사용하여 A0 핀의 에러를 방지합니다.
turb_channel = AnalogIn(ads, 0)

print("🚀 탁도 센서 5V 실시간 테스트를 시작합니다!")
print("종료하려면 Ctrl+C를 누르세요.\n")

# 4. 실시간 측정 루프
while True:
    try:
        # 가공되지 않은 순수 아날로그 전압 읽기 (보정 계수 1.5 삭제됨)
        raw_voltage = turb_channel.voltage

        # 수질 상태 텍스트 변환
        status = "맑음 (정상)"
        if raw_voltage < 2.5:
            status = "매우 흐림 (심각한 오염)"
        elif raw_voltage < 4.0:
            status = "흐림 (오염 감지됨)"

        # 결과 출력 (소수점 2자리까지)
        print(f"💧 탁도 센서 측정 전압: {raw_voltage:.2f}V | 현재 상태: {status}")
        
        # 0.5초마다 데이터 갱신
        time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n🛑 테스트를 안전하게 종료합니다.")
        break
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        time.sleep(1)
