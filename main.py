import os
import time
import subprocess
from datetime import datetime
from google import genai
from dotenv import load_dotenv

load_dotenv()

def _read_int_env(name, default):
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default

def _read_text_env(name, default):
    raw_value = os.getenv(name, "").strip()
    return raw_value or default

class HMTStoreMonitor:
    def __init__(self, store_id, rtsp_url):
        self.store_id = store_id
        self.rtsp_url = rtsp_url
        self.local_path = os.getenv("HMT_CLIPS_DIR", "/tmp/hmt/clips")
        self.target_jid = os.getenv("HMT_TARGET_JID", "120363425686019694@g.us")
        self.bot_tool_path = os.getenv(
            "HMT_BOT_TOOL_PATH",
            "/home/ubuntu/whatsapp-baileys-bot-migration/tools/send_whatsapp_message.mjs"
        )
        self.sub_rtsp_url = os.getenv(
            "HMT_RTSP_URL_SUB",
            "rtsp://admin:Hello1234@192.168.1.113:554/h264Preview_01_sub"
        )
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self._ai_client = None
        os.makedirs(self.local_path, exist_ok=True)

    def get_ai_client(self):
        if not self.api_key:
            raise RuntimeError("搵唔到 GEMINI_API_KEY，無法做 AI 分析。")
        if self._ai_client is None:
            self._ai_client = genai.Client(api_key=self.api_key)
        return self._ai_client

    def cleanup_old_clips(self, days=3):
        """ 自動刪除舊片 """
        now = time.time()
        cutoff = now - (days * 86400)
        for f in os.listdir(self.local_path):
            file_path = os.path.join(self.local_path, f)
            if f.endswith(".partial"):
                continue
            if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff:
                os.remove(file_path)

    def capture_clip(self, duration=300):
        """ 使用 FFmpeg 錄製影片 """
        try:
            self.cleanup_old_clips(days=3)
        except Exception:
            pass
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.store_id}_{timestamp}.mp4"
        filepath = os.path.join(self.local_path, filename)
        partial_filepath = os.path.join(self.local_path, f"{self.store_id}_{timestamp}.partial.mp4")

        quality_profile = _read_text_env("HMT_RECORD_QUALITY", "medium").lower()
        input_rtsp_url = self.rtsp_url
        source_label = "main"
        command = [
            "ffmpeg", "-y", "-rtsp_transport", "tcp",
            "-i", input_rtsp_url,
            "-t", str(duration)
        ]

        if quality_profile == "high":
            print(f"🎥 [{self.store_id}] 正在錄製 {duration}秒 片段... (quality=high, source=main)")
            command.extend([
                "-c", "copy",
                "-movflags", "+faststart",
                "-tag:v", "hvc1",
                partial_filepath
            ])
        elif quality_profile == "low":
            input_rtsp_url = self.sub_rtsp_url
            source_label = "sub"
            command[5] = input_rtsp_url
            print(f"🎥 [{self.store_id}] 正在錄製 {duration}秒 片段... (quality=low, source={source_label})")
            command.extend([
                "-vf", "scale=640:-2,fps=8",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", str(_read_int_env("HMT_RECORD_CRF", 31)),
                "-maxrate", _read_text_env("HMT_RECORD_MAXRATE", "900k"),
                "-bufsize", _read_text_env("HMT_RECORD_BUFSIZE", "1800k"),
                "-c:a", "aac",
                "-b:a", _read_text_env("HMT_RECORD_AUDIO_BITRATE", "32k"),
                "-ac", "1",
                "-movflags", "+faststart",
                partial_filepath
            ])
        else:
            input_rtsp_url = self.sub_rtsp_url
            source_label = "sub"
            command[5] = input_rtsp_url
            print(f"🎥 [{self.store_id}] 正在錄製 {duration}秒 片段... (quality=medium, source={source_label})")
            command.extend([
                "-c", "copy",
                "-movflags", "+faststart",
                "-tag:v", "avc1",
                partial_filepath
            ])
        
        try:
            if os.path.exists(partial_filepath):
                os.remove(partial_filepath)
            timeout_seconds = duration + _read_int_env("HMT_CAPTURE_TIMEOUT_EXTRA", 120)
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds)
            if result.returncode == 0 and os.path.exists(partial_filepath) and os.path.getsize(partial_filepath) > 0:
                os.replace(partial_filepath, filepath)
                print(f"✅ 成功儲存: {filepath}")
                return filepath
            else:
                stderr_tail = (result.stderr or "").strip()[-500:]
                print(f"❌ 錄製失敗: {stderr_tail or 'ffmpeg 無輸出可參考'}")
                if os.path.exists(partial_filepath):
                    try:
                        os.remove(partial_filepath)
                    except OSError:
                        pass
                return None
        except Exception as e:
            print(f"❌ 錄製異常: {e}")
            if os.path.exists(partial_filepath):
                try:
                    os.remove(partial_filepath)
                except OSError:
                    pass
            return None

    def analyze_behavior(self, video_path):
        """ 使用 Gemini 分析巡舖片段 """
        print(f"🤖 正在分析巡舖片段: {os.path.basename(video_path)}")
        try:
            client = self.get_ai_client()
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
    STORE_ID = os.getenv("HMT_STORE_ID", "CM234")
    RTSP_URL = os.getenv("HMT_RTSP_URL", "rtsp://admin:Hello1234@192.168.1.113:554/h264Preview_01_main")
    probe_duration = _read_int_env("HMT_PROBE_DURATION", 5)
    bot = HMTStoreMonitor(STORE_ID, RTSP_URL)
    print(f"🧪 正在手動測試連線... ({probe_duration} 秒)")
    path = bot.capture_clip(duration=probe_duration)
    if path:
        print(f"🎉 測試成功！文件: {path}")
