import os
from google import genai
from dotenv import load_dotenv

# 1. 初始化
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def analyze_screenshots(folder_path):
    print(f"🔍 正在分析截圖目錄: {folder_path}")
    frames = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".png")]
    
    if not frames:
        print("❌ 搵唔到截圖。")
        return

    try:
        # 上傳截圖
        uploaded_files = []
        for frame in frames[:2]: # 淨係睇兩張
            print(f"📤 上傳中: {frame}")
            f = client.files.upload(file=frame)
            uploaded_files.append(f)

        print("\n🔍 正在叫 Gemini 解讀鏡頭環境...")

        prompt = """
        妳宜家係一個專業嘅安防與零售顧問。請睇吓呢兩張 HMT 店舖嘅截圖，然後話我知：
        1. 呢個鏡頭嘅安裝位置同視角係點樣？(例如：高位俯視、正對門口、影住收銀位等)
        2. 鏡頭嘅覆蓋範圍影到舖頭邊幾個關鍵區域？(例如：衫架區、試身室門口、收銀台、正門入口)
        3. 畫面入面最明顯嘅物件係乜嘢？
        4. 根據呢個特定嘅視角，妳認為 AI 最適合用嚟檢測邊啲「對舖頭營運有用」嘅資訊？
        
        請用廣東話回答。
        """
        
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=uploaded_files + [prompt]
        )

        print("\n=== 📸 鏡頭環境診斷結果 ===")
        print(response.text)
        print("==========================")

        # 清理
        for f in uploaded_files:
            client.files.delete(name=f.name)

    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")

if __name__ == "__main__":
    folder = "/home/ubuntu/ai-webcam-intelligence-system/screenshots"
    analyze_screenshots(folder)
