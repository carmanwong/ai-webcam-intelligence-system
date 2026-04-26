import time
import os
from datetime import datetime
from queue import Empty, Queue
from threading import Event, Thread
from main import HMTStoreMonitor

DEFAULT_RTSP_URL = "rtsp://admin:Hello1234@192.168.1.113:554/h264Preview_01_main"

def read_int_env(name, default):
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default

def read_bool_env(name, default):
    raw_value = os.getenv(name, "").strip().lower()
    if not raw_value:
        return default
    return raw_value in {"1", "true", "yes", "on"}

STORE_ID = os.getenv("HMT_STORE_ID", "CM234")
RTSP_URL = os.getenv("HMT_RTSP_URL", DEFAULT_RTSP_URL)
CLIP_DURATION = read_int_env("HMT_CLIP_DURATION", 300)
ANALYSIS_INTERVAL = read_int_env("HMT_ANALYSIS_INTERVAL", 900)
RETRY_DELAY = read_int_env("HMT_RETRY_DELAY", 5)
IDLE_SLEEP = read_int_env("HMT_IDLE_SLEEP", 60)
OPERATING_START = os.getenv("HMT_OPERATING_START", "08:00")
OPERATING_END = os.getenv("HMT_OPERATING_END", "22:45")
ENABLE_ANALYSIS = read_bool_env("HMT_ENABLE_ANALYSIS", True)

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def parse_clock(value):
    return datetime.strptime(value, "%H:%M").time()

def is_operating_hours():
    now = datetime.now().time()
    start_time = parse_clock(OPERATING_START)
    end_time = parse_clock(OPERATING_END)
    return start_time <= now <= end_time

class AnalysisWorker:
    def __init__(self, bot, enabled):
        self.bot = bot
        self.enabled = enabled
        self.queue = Queue(maxsize=1)
        self.stop_event = Event()
        self.thread = None

        if self.enabled:
            self.thread = Thread(target=self.run, daemon=True)
            self.thread.start()

    def enqueue(self, clip_path):
        if not self.enabled:
            return False
        if self.queue.full():
            return False
        self.queue.put(clip_path)
        return True

    def stop(self):
        self.stop_event.set()

    def run(self):
        while not self.stop_event.is_set():
            try:
                clip_path = self.queue.get(timeout=1)
            except Empty:
                continue

            try:
                log(f"🧠 開始 AI 分析: {os.path.basename(clip_path)}")
                report = self.bot.analyze_behavior(clip_path)
                if report:
                    self.bot.send_whatsapp_report(report)
                    log("✅ AI 報告已發送到 WhatsApp")
                else:
                    log("⚠️ AI 分析未產生報告")
            except Exception as error:
                log(f"❌ AI worker 異常: {error}")
            finally:
                self.queue.task_done()

def run_continuous_recorder():
    bot = HMTStoreMonitor(STORE_ID, RTSP_URL)
    analysis_worker = AnalysisWorker(bot, ENABLE_ANALYSIS)
    last_analysis_time = 0.0
    last_idle_notice = ""

    log(
        f"🚀 HMT Recorder 啟動 "
        f"(store={STORE_ID}, clip={CLIP_DURATION}s, analysis={'on' if ENABLE_ANALYSIS else 'off'}, "
        f"hours={OPERATING_START}-{OPERATING_END})"
    )

    try:
        while True:
            if not is_operating_hours():
                idle_key = datetime.now().strftime("%Y-%m-%d %H:%M")
                if idle_key != last_idle_notice:
                    log(f"😴 非營業時間，休眠中 ({OPERATING_START}-{OPERATING_END})")
                    last_idle_notice = idle_key
                time.sleep(IDLE_SLEEP)
                continue

            last_idle_notice = ""
            log(f"🎬 正在錄製 {CLIP_DURATION} 秒高畫質片段...")
            clip_path = bot.capture_clip(duration=CLIP_DURATION)

            if not clip_path:
                log(f"⚠️ 錄影失敗，{RETRY_DELAY} 秒後重試...")
                time.sleep(RETRY_DELAY)
                continue

            log(f"✅ 新片段已儲存: {os.path.basename(clip_path)}")

            current_time = time.time()
            if ENABLE_ANALYSIS and current_time - last_analysis_time >= ANALYSIS_INTERVAL:
                if analysis_worker.enqueue(clip_path):
                    last_analysis_time = current_time
                    log(f"🧠 已排隊 AI 分析: {os.path.basename(clip_path)}")
                else:
                    log("⚠️ AI 分析仍在忙碌，今次先跳過，錄影繼續。")
    finally:
        analysis_worker.stop()

if __name__ == "__main__":
    run_continuous_recorder()
