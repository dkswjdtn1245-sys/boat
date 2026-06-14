import serial
import time

print("🚀 레이저 센서(TF-Luna) 단독 테스트를 시작합니다.")

# 1. 시리얼 포트 열기
try:
    ser = serial.Serial('/dev/serial0', 115200, timeout=0.1)
    print("✅ 시리얼 포트(/dev/serial0) 연결 성공!")
except Exception as e:
    print(f"❌ 시리얼 포트 열기 실패: {e}")
    print("💡 힌트: sudo raspi-config 에서 Serial Port가 열려있는지 확인하세요.")
    exit()

# 2. 데이터 읽기 함수 (버퍼 찌꺼기 완벽 처리)
# --- 수정된 강력한 데이터 읽기 함수 ---
def read_tfluna():
    ser.reset_input_buffer() # 찌꺼기 싹 비우기
    time.sleep(0.02)         # 센서가 새 데이터 9바이트를 쏠 때까지 잠깐 대기
    
    if ser.in_waiting >= 9:
        data = ser.read(9)   # 1바이트씩 찔끔 읽지 말고, 9바이트를 한 번에 캡처!
        
        # 첫 번째와 두 번째 데이터가 'Y'(0x59) 인지 확인해서 줄이 맞는지 체크
        if data[0] == 0x59 and data[1] == 0x59: 
            distance = data[2] + (data[3] << 8)
            strength = data[4] + (data[5] << 8)
            temperature = (data[6] + (data[7] << 8)) / 8.0 - 256.0
            return distance, strength, temperature
            
    return -1, -1, -1
# 3. 메인 무한 루프
try:
    print("🎯 거리 측정을 시작합니다. 센서 앞에 손을 흔들어보세요! (종료: Ctrl+C)")
    ser.reset_input_buffer() # 시작 전 버퍼 싹 비우기
    
    while True:
        dist, strength, temp = read_tfluna()
        
        if dist != -1:
            print(f"📏 거리: {dist:4d} cm | 📶 신호 강도: {strength:5d} | 🌡️ 온도: {temp:.1f}°C")
        else:
            # 데이터를 못 받았을 때 출력
            print("⏳ 데이터 수신 실패... (선이 빠졌거나 TX/RX가 반대입니다)")
            
        time.sleep(0.1) # 0.1초마다 아주 빠르게 측정 (10Hz)

except KeyboardInterrupt:
    print("\n🛑 테스트를 종료합니다.")
    ser.close()
