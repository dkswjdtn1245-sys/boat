import serial
import time

# 시리얼 포트 설정
ser = serial.Serial("/dev/serial0", 115200, timeout=1)

def read_tfluna_uart():
    while True:
        try:
            # 1. 첫 번째 헤더 0x59가 나올 때까지 1바이트씩 계속 읽으며 전진
            if ser.read(1) == b'\x59':
                # 2. 첫 번째 0x59를 찾았다면, 바로 다음 바이트가 또 0x59인지 확인
                if ser.read(1) == b'\x59':
                    
                    # 3. 완벽한 헤더(0x59, 0x59)를 찾았으므로, 나머지 데이터 7바이트를 통째로 읽음
                    remaining = ser.read(7)
                    if len(remaining) < 7:
                        continue # 만약 데이터가 중간에 잘렸다면 이번 패킷은 버리고 다시 시도
                    
                    # 4. 데이터 파싱 (나머지 7바이트 배열이므로 인덱스가 2씩 당겨짐)
                    distance = remaining[0] + remaining[1] * 256      # 단위: cm
                    strength = remaining[2] + remaining[3] * 256      # 신호 강도
                    temperature = remaining[4] + remaining[5] * 256
                    temperature = (temperature / 8.0) - 256.0          # 내부 온도
                    
                    return distance, strength, temperature
                    
        except Exception as e:
            print(f"시리얼 통신 일시 오류 예외 처리: {e}")
            
        time.sleep(0.001) # 라즈베리파이 CPU 과부하 방지용 미세 딜레이

if __name__ == "__main__":
    try:
        print("=== TF-Luna 락 현상 방지 완벽 동기화 버전 시작 ===")
        if not ser.is_open:
            ser.open()
            
        while True:
            dist, strg, temp = read_tfluna_uart()
            print(f"거리: {dist} cm ({dist/100:.2f} m) | 신호 강도: {strg} | 센서 온도: {temp:.1f} °C")
            time.sleep(0.1) # 0.1초 주기로 실시간 출력
            
    except KeyboardInterrupt:
        print("\n테스트를 종료합니다.")
    finally:
        ser.close()
