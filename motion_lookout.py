import cv2
import os
import time
import subprocess
from datetime import datetime

# 配置
RTSP_URL_SUB = os.getenv("HMT_RTSP_URL_SUB", "rtsp://admin:Hello1234@192.168.1.113:554/h264Preview_01_sub")
RTSP_URL_MAIN = os.getenv("HMT_RTSP_URL_MAIN", "rtsp://admin:Hello1234@192.168.1.113:554/h264Preview_01_main")
OUTPUT_DIR = os.getenv("HMT_MOTION_OUTPUT_DIR", "/tmp/hmt/clips_motion")
THRESHOLD = 300000 
CHECK_INTERVAL = 3   # 縮短檢查間隔，反應更快
GRACE_PERIOD = 30    # 發現無人後，再多錄 30 秒保險期

def get_snapshot():
    filename = os.getenv("HMT_MOTION_SNAPSHOT_PATH", "/tmp/hmt/motion_check_live.jpg")
    cmd = ["ffmpeg", "-y", "-rtsp_transport", "tcp", "-i", RTSP_URL_SUB, "-frames:v", "1", "-q:v", "5", filename]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
        return cv2.imread(filename)
    except: return None

def run_smart_lookout():
    print("🚀 HMT Smart Motion Tracker 啟動")
    prev_frame = None
    recording_proc = None
    last_motion_time = 0
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    while True:
        curr_frame = get_snapshot()
        if curr_frame is None:
            time.sleep(5)
            continue

        # 1. 動作偵測邏輯
        gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        has_motion = False
        if prev_frame is not None:
            delta = cv2.absdiff(prev_frame, gray)
            thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
            score = cv2.countNonZero(thresh)
            print(f"📊 [DEBUG] 當前變動分數: {score} (門檻: {THRESHOLD})")
            if score > THRESHOLD:

                has_motion = True
                last_motion_time = time.time()
                # print(f"🔥 偵測到動作！ (Score: {score})")

        prev_frame = gray

        # 2. 錄影狀態機 (State Machine)
        if has_motion:
            if recording_proc is None:
                # 代表新發現，開始錄影
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"MOTION_{timestamp}.mp4"
                filepath = os.path.join(OUTPUT_DIR, filename)
                print(f"🎥 [{datetime.now().strftime('%H:%M:%S')}] 有人入嚟喇！開始追蹤錄影...")
                
                # 開始背景錄影 (唔設 -t，手動控制幾時停)
                cmd = ["ffmpeg", "-y", "-rtsp_transport", "tcp", "-i", RTSP_URL_MAIN, "-c", "copy", filepath]
                recording_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # 已經錄緊，因為見到人，所以繼續錄
                pass
        else:
            # 目前畫面靜止
            if recording_proc is not None:
                idle_time = time.time() - last_motion_time
                if idle_time > GRACE_PERIOD:
                    # 已經 30 秒無人郁，可以收掣
                    print(f"🛑 [{datetime.now().strftime('%H:%M:%S')}] 無人郁超過 30 秒，停止追蹤。")
                    recording_proc.terminate()
                    recording_proc = None
                else:
                    # 雖然呢一秒無人，但仲喺 30 秒保險期內，繼續錄
                    # print(f"⏳ 等待冷靜中... ({int(GRACE_PERIOD - idle_time)}s)")
                    pass

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_smart_lookout()
