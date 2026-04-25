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
        os.makedirs(self.local_path, exist_ok=True)

    def capture_clip(self, duration=10):
        """ 使用 FFmpeg 錄製影片 """
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
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✅ 成功儲存: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ 錄製失敗: {e}")
            return None

    def analyze_behavior(self, video_path):
        """ 使用 Gemini 分析店員行為與客流 """
        print(f"🤖 正在分析店員動態...")
        
        try:
            # 上傳影片
            video_file = client.files.upload(file=video_path)
            
            # 等待處理
            while video_file.state == "PROCESSING":
                time.sleep(2)
                video_file = client.files.get(name=video_file.name)

            # 開放式、高智能分析 Prompt
            prompt = f"""
            妳宜家係 Hello Milk Tee (HMT) 嘅「隱形巡舖專家」。這段 (ID: {self.store_id}) 嘅監控片段係妳嘅觀察對象。
            
            唔好淨係死板咁回答問題。請妳運用妳嘅高智能，為老闆提供一份「有深度、有溫度」嘅營運洞察：
            
            1. [現場實況]: 快速描述店員與客人嘅互動、位置與狀態。
            2. [深度發現]: 妳見到啲乜嘢「特別」嘅細節？(例如：客人攞起某件衫睇咗好耐但無試、店員分心處理緊啲乜、舖頭動線係咪順暢、或者某個陳列位有無發揮作用？)
            3. [專家建議]: 根據妳見到嘅嘢，妳會建議老闆呢一刻注意啲乜？
            
            請用道地廣東話、以 WhatsApp 格式報告。要有亮點，唔好講廢話。
            
            格式參考：
            📍 HMT {self.store_id} 巡舖即時洞察
            ---
            (妳嘅全方位觀察與深度分析，用 Emoji 標示重點)
            
            💡 老闆妳可能無發現...
            (妳獨到嘅觀察細節)
            """
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[video_file, prompt]
            )

            report = response.text
            print("\n--- 📝 生成報告 ---")
            print(report)
            print("------------------")
            
            # 清理
            client.files.delete(name=video_file.name)
            return report

        except Exception as e:
            print(f"❌ 分析失敗: {e}")
            return None

if __name__ == "__main__":
    # 測試流程
    STORE_ID = "CM234"
    # 呢度可以用妳真正嘅 RTSP URL
    RTSP_URL = "rtsp://admin:admin12345@100.125.176.71:554/Preview_1" 
    
    bot = HMTStoreMonitor(STORE_ID, RTSP_URL)
    
    # 1. 錄製
    # clip = bot.capture_clip(10)
    
    # 2. 如果無錄製，就用返妳個測試檔做 Demo
    TEST_FILE = "/home/ubuntu/clips/cm234_test.mp4"
    if os.path.exists(TEST_FILE):
        bot.analyze_behavior(TEST_FILE)
    else:
        print("❌ 搵唔到測試片")
