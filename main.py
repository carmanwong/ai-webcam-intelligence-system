import os
import time
import subprocess
from datetime import datetime
from google import genai
from dotenv import load_dotenv

# 1. 初始化與環境檢查
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ 錯誤: 搵唔到 GEMINI_API_KEY")
    exit(1)

client = genai.Client(api_key=API_KEY)

class HMTStoreMonitor:
    def __init__(self, store_id, rtsp_url):
        self.store_id = store_id
        self.rtsp_url = rtsp_url
        self.local_path = "/home/ubuntu/clips"
        self.target_jid = "120363425686019694@g.us" # Cam 234 📹
        self.bot_tool_path = "/home/ubuntu/whatsapp-baileys-bot-migration/tools/send_whatsapp_message.mjs"
        os.makedirs(self.local_path, exist_ok=True)

    def cleanup_old_clips(self, days=3):
        """ 自動刪除舊片 """
        now = time.time()
        cutoff = now - (days * 86400)
        for f in os.listdir(self.local_path):
            file_path = os.path.join(self.local_path, f)
            if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff:
                os.remove(file_path)

    def capture_clip(self, duration=300):
        """ 使用 FFmpeg 錄製影片 """
        try:
            self.cleanup_old_clips(days=3)
        except:
            pass
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.store_id}_{timestamp}.mp4"
        filepath = os.path.join(self.local_path, filename)

        print(f"🎥 [{self.store_id}] 正在錄製 {duration}秒 片段...")
        command = [
            "ffmpeg", "-y", "-rtsp_transport", "tcp",
            "-i", self.rtsp_url,
            "-t", str(duration),
            "-c", "copy", filepath
        ]
        
        try:
            # 增加連線超時，支持高畫質大檔案
            result = subprocess.run(command, capture_output=True, text=True, timeout=duration + 120)
            if result.returncode == 0:
                print(f"✅ 成功儲存: {filepath}")
                return filepath
            else:
                print(f"❌ 錄製失敗: {result.stderr[-100:]}")
                return None
        except Exception as e:
            print(f"❌ 錄製異常: {e}")
            return None

    def analyze_behavior(self, video_path):
        """ 使用 Gemini 分析巡舖片段 """
        print(f"🤖 正在分析巡舖片段: {os.path.basename(video_path)}")
        try:
            video_file = client.files.upload(file=video_path)
            while video_file.state == "PROCESSING":
                time.sleep(2)
                video_file = client.files.get(name=video_file.name)

            prompt = f"""
            妳宜家係 HMT 嘅「隱形巡舖專家」。這段 (ID: {self.store_id}) 嘅監控片段係妳嘅觀察對象。
            請運用妳嘅高智能提供一份「有深度、有溫度」嘅廣東話營運洞察：
            
            1. [現場實況]: 快速描述店員與客人嘅互動、位置與狀態。
            2. [深度發現]: 妳見到啲乜嘢「特別」嘅細節？
            3. [專家建議]: 妳會建議老闆呢一刻注意啲乜？
            
            請用廣東話、以 WhatsApp 格式報告。
            💡 老闆妳可能無發現... (寫出獨到細節)
            """
            
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[video_file, prompt]
            )
            report = response.text
            client.files.delete(name=video_file.name)
            return report
        except Exception as e:
            print(f"❌ 分析失敗: {e}")
            return None

    def send_whatsapp_report(self, report_text):
        """ 透過橋樑工具發送報告 """
        if not report_text: return
        command = ["node", self.bot_tool_path, "--jid", self.target_jid, "--text", report_text, "--send"]
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
            print("✅ WhatsApp 報告已發送")
        except:
            print("❌ WhatsApp 發送失敗")

if __name__ == "__main__":
    STORE_ID = "CM234"
    RTSP_URL = "rtsp://admin:Hello1234@192.168.1.113:554/h264Preview_01_main"
    bot = HMTStoreMonitor(STORE_ID, RTSP_URL)
    print("🧪 正在手動測試連線...")
    path = bot.capture_clip(duration=5)
    if path:
        print(f"🎉 測試成功！文件: {path}")
