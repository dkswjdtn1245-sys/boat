import serial
import time

# 라즈베리파이 미니 UART 포트 및 보레이트 설정 (기본 115200)
ser = serial.Serial("/dev/serial0", 115200, timeout=1)

def read_tfluna_uart():
    while True:
        # 시리얼 버퍼에 9바이트 이상 쌓였는지 확인
        if ser.in_waiting >= 9:
            bytes_serial = ser.read(9)
            ser.reset_input_buffer()
            
            # TF-Luna 데이터 프레임 헤더(0x59, 0x59) 검증
            if bytes_serial[0] == 0x59 and bytes_serial[1] == 0x59:
                distance = bytes_serial[2] + bytes_serial[3] * 256      # 단위: cm
                strength = bytes_serial[4] + bytes_serial[5] * 256      # 신호 강도 (적정 수치 > 100)
                temperature = bytes_serial[6] + bytes_serial[7] * 256
                temperature = (temperature / 8.0) - 256.0              # 칩 내부 온도 변환
                
                return distance, strength, temperature
        time.sleep(0.01)

if __name__ == "__main__":
    try:
        print("=== TF-Luna UART 모드 테스트 시작 ===")
        if not ser.is_open:
            ser.open()
            
        while True:
            dist, strg, temp = read_tfluna_uart()
            print(f"거리: {dist} cm ({dist/100:.2f} m) | 신호 강도: {strg} | 센서 온도: {temp:.1f} °C")
            time.sleep(0.2) # 0.2초 간격 출력
            
    except KeyboardInterrupt:
        print("\n테스트를 종료합니다.")
    finally:
        ser.close()
