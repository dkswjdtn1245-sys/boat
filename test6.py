import serial
import time

# [설정] 내 라즈베리파이에 인식된 USB 포트명과 속도 기입
SERIAL_PORT = '/dev/ttyACM0'  # 만약 위에서 ttyACM0로 나왔다면 수정해줘
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"==================================================")
    print(f" [{SERIAL_PORT}] TEL0138 USB GPS 연결 성공!")
    print(f" 데이터 수신 대기 중... (종료하려면 Ctrl+C)")
    print(f"==================================================")
except Exception as e:
    print(f"❌ 포트 열기 실패: {e}")
    print("TIP: USB를 다시 뽑았다 꽂거나 'ls /dev/ttyUSB*'로 포트명을 재확인하세요.")
    exit()

while True:
    try:
        if ser.in_waiting > 0:
            # 시리얼 한 줄 읽기 및 디코딩
            raw_line = ser.readline()
            line = raw_line.decode('utf-8', errors='ignore').strip()
            
            # GPS 데이터(NMEA 표준 문장) 확인
            if line.startswith('$'):
                # 1. 원시 NMEA 문장 출력 (센서가 살아있는지 1차 확인용)
                print(f"[Raw NMEA]: {line}")
                
                # 2. 추천 최소 데이터가 담긴 RMC(Recommended Minimum Navigation Information) 문장 파싱
                # 예시: $GNRMC,051020.00,A,3506.1234,N,12904.5678,E,...
                if "RMC" in line:
                    parts = line.split(',')
                    
                    # 데이터 개수가 충분하고 상태가 'A'(Active, 수신 성공)인지 확인
                    if len(parts) > 6:
                        status = parts[2]
                        if status == 'A':
                            raw_lat = parts[3]  # DDMM.MMMM 포맷 위도
                            lat_dir = parts[4]  # N 또는 S
                            raw_lon = parts[5]  # DDDMM.MMMM 포맷 경도
                            lon_dir = parts[6]  # E 또는 W
                            
                            print(f"\n✨ [위치 고정 완료] ----------------------------")
                            print(f" 📍 위도(Raw): {raw_lat} {lat_dir}")
                            print(f" 📍 경도(Raw): {raw_lon} {lon_dir}")
                            print(f"----------------------------------------------\n")
                        else:
                            print(" ⚠️ [위치 탐색 중] 센서 연결은 정상이나 위성 신호를 잡지 못했습니다.")
                            
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 테스트가 종료되었습니다.")
        ser.close()
        break
    except Exception as e:
        print(f"오류 발생: {e}")
        time.sleep(1)
