import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 1. 初始化
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def test_analysis(video_path):
    print(f"🎬 測試影片: {video_path}")
    
    try:
        # 2. 上傳影片
        print("📤 正在上傳影片到 Google...")
        video_file = client.files.upload(file=video_path)
        print(f"✅ 上傳成功，文件 ID: {video_file.name}")

        # 3. 等待處理
        print("⏳ 處理中", end="")
        while video_file.state == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(3)
            video_file = client.files.get(name=video_file.name)
        
        if video_file.state == "FAILED":
            print(f"\n❌ 處理失敗")
            return

        print("\n🔍 處理完成，開始分析...")

        # 4. 生成內容
        prompt = "呢段係舖頭嘅監控片段。請分析：1. 人流狀況 2. 店員喺度做緊乜？ 3. 舖頭整潔度。請用廣東話回答。"
        
        response = client.models.generate_content(
            model="gemini-flash-latest", # 使用最新最強嘅 2.0 Flash
            contents=[video_file, prompt]
        )

        print("\n=== ✨ Gemini 分析結果 ===")
        print(response.text)
        print("==========================")

        # 5. 清理
        client.files.delete(name=video_file.name)
        print("\n🧹 已清理暫存檔案。")

    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")

if __name__ == "__main__":
    video = "/home/ubuntu/clips/cm234_test.mp4"
    test_analysis(video)
