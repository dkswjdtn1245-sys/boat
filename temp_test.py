import os
import glob
import time

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
print("======= DS18B20 수온 센서 연결 테스트 =======")

try:
    device_folder = glob.glob(base_dir + '28*')[0]
    device_file = device_folder + '/w1_slave'
    print(f"🚀 센서 인식 성공! (ID: {device_folder.split('/')[-1]})")
except IndexError:
    print("❌ 수온 센서를 찾을 수 없습니다. 선 연결을 확인하세요.")
    exit()

def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        return float(temp_string) / 1000.0

print("실시간 수온 측정 중... (종료: Ctrl + C)")
try:
    while True:
        print(f"💧 현재 수온: {read_temp():.2f} °C")
        time.sleep(1)
except KeyboardInterrupt:
    print("\n👋 종료합니다.")
