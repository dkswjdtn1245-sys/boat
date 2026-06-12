import os
import glob
import time

# 1-Wire 커널 모듈 활성화
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# DS18B20 디바이스 파일 경로 찾기
base_dir = '/sys/bus/w1/devices/'
device_folders = glob.glob(base_dir + '28*')

if not device_folders:
    print("❌ DS18B20 센서를 찾을 수 없습니다.")
    print("연결 상태(VCC, GND, 데이터 핀) 및 /boot/config.txt 설정을 확인하세요.")
    exit()

# 발견된 첫 번째 센서의 경로 지정
device_file = device_folders[0] + '/w1_slave'
print(f"✅ 센서 연결 확인됨: {device_folders[0].split('/')[-1]}")

def read_temp_raw():
    """시스템 센서 파일에서 로우 데이터(텍스트)를 읽어옵니다."""
    with open(device_file, 'r') as f:
        lines = f.readlines()
    return lines

def read_temp():
    """로우 데이터를 파싱하여 섭씨 온도(°C)로 반환합니다."""
    lines = read_temp_raw()
    
    # 통신 성공 여부 확인 (YES로 끝나야 함)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
        
    # 't=' 문자열 뒤에 있는 온도 데이터 추출
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0  # 시스템 값은 밀리도 단위이므로 1000으로 나눔
        return temp_c

# 메인 루프 실행
try:
    print("\n🌡️ 실시간 수온 측정 시작... (종료하려면 Ctrl+C를 누르세요)")
    print("-" * 40)
    
    while True:
        temperature = read_temp()
        print(f"현재 수온: {temperature:.2f} °C")
        time.sleep(1.0) # 1초 간격 측정

except KeyboardInterrupt:
    print("\n👋 측정을 종료합니다.")
