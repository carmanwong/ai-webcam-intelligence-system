import time
import os
from datetime import datetime
from main import HMTStoreMonitor

# 配置
STORE_ID = "CM234"
RTSP_URL = "rtsp://admin:Hello1234@192.168.1.113:554/h264Preview_01_sub"
CLIP_DURATION = 300  # 5 分鐘一段
ANALYSIS_INTERVAL = 900  # 每 15 分鐘一次 AI 報告

def is_operating_hours():
    """ 營業時間：08:00 - 22:45 """
    now = datetime.now().time()
    start_time = datetime.strptime("08:00", "%H:%M").time()
    end_time = datetime.strptime("22:45", "%H:%M").time()
    return start_time <= now <= end_time

def run_continuous_recorder():
    print(f"🚀 HMT 5分鐘一段錄影系統啟動 ({STORE_ID})")
    print(f"⏰ 營業時間：08:00 - 22:45")
    print(f"📊 報告頻率：每 15 分鐘分析一次")
    
    bot = HMTStoreMonitor(STORE_ID, RTSP_URL)
    last_analysis_time = 0
    
    while True:
        if is_operating_hours():
            print(f"🎬 [{datetime.now().strftime('%H:%M:%S')}] 開始錄製新片段...")
            clip_path = bot.capture_clip(duration=CLIP_DURATION)
            
            if clip_path:
                current_time = time.time()
                if current_time - last_analysis_time >= ANALYSIS_INTERVAL:
                    print(f"🧠 正在執行 AI 巡舖分析...")
                    report = bot.analyze_behavior(clip_path)
                    if report:
                        bot.send_whatsapp_report(report)
                    last_analysis_time = current_time
            else:
                print("⚠️ 錄影失敗，10 秒後重試...")
                time.sleep(10)
        else:
            print(f"😴 [{datetime.now().strftime('%H:%M:%S')}] 非營業時間，休眠中...")
            time.sleep(60)

if __name__ == "__main__":
    run_continuous_recorder()
