import serial
import time

# 시리얼 포트 설정
ser = serial.Serial("/dev/serial0", 115200, timeout=1)

def read_tfluna_uart():
    while True:
        try:
            if ser.in_waiting >= 9:
                bytes_serial = ser.read(9)
                
                # 🚨 [안전장치 1] 순간 잡음으로 데이터가 9바이트 미만이면 무시하고 다시 읽기
                if len(bytes_serial) < 9:
                    continue
                
                # TF-Luna 데이터 프레임 헤더(0x59, 0x59) 검증
                if bytes_serial[0] == 0x59 and bytes_serial[1] == 0x59:
                    distance = bytes_serial[2] + bytes_serial[3] * 256      # 단위: cm
                    strength = bytes_serial[4] + bytes_serial[5] * 256      # 신호 강도
                    temperature = bytes_serial[6] + bytes_serial[7] * 256
                    temperature = (temperature / 8.0) - 256.0              # 내부 온도
                    
                    # 버퍼를 비워 실시간 최신 데이터 유지
                    ser.reset_input_buffer()
                    return distance, strength, temperature
                    
        except Exception as e:
            # 🚨 [안전장치 2] 물리적 끊김 등 에러가 나도 스크립트가 죽지 않도록 예외 처리
            print(f"통신 일시 오류 무시: {e}")
            
        time.sleep(0.01)

if __name__ == "__main__":
    try:
        print("=== TF-Luna 예외 처리 보완 버전 테스트 시작 ===")
        if not ser.is_open:
            ser.open()
            
        while True:
            dist, strg, temp = read_tfluna_uart()
            print(f"거리: {dist} cm ({dist/100:.2f} m) | 신호 강도: {strg} | 센서 온도: {temp:.1f} °C")
            time.sleep(0.1) # 출력 주기 0.1초로 상향
            
    except KeyboardInterrupt:
        print("\n테스트를 종료합니다.")
    finally:
        ser.close()
