import os
import subprocess
import time
from datetime import datetime
# import boto3  # 用於 Cloudflare R2 上傳

class AIWebcamBot:
    def __init__(self, store_id, rtsp_url):
        self.store_id = store_id
        self.rtsp_url = rtsp_url
        self.local_path = "./clips"
        os.makedirs(self.local_path, exist_ok=True)

    def capture_clip(self, duration=10):
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

    def upload_to_r2(self, local_file):
        """
        待實現：使用 boto3 上傳到 Cloudflare R2
        """
        print(f"☁️ 正在上傳 {local_file} 到 Cloudflare R2...")
        # TODO: Implement R2 upload logic
        pass

    def run_ai_analysis(self, r2_url):
        """
        待實現：呼叫 Gemini 1.5 Pro API
        """
        print(f"🤖 正在呼叫 Gemini 分析片段: {r2_url}")
        # TODO: Implement Gemini API logic
        pass

if __name__ == "__main__":
    # 測試用：CM234 舖頭
    TEST_RTSP = "rtsp://admin:password@192.168.1.113:554/h264Preview_01_sub"
    bot = AIWebcamBot("CM234", TEST_RTSP)
    
    # 執行一次任務
    file = bot.capture_clip(15)
    if file:
        bot.upload_to_r2(file)
