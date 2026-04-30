import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai


DEFAULT_PROMPT = """呢條片係舖頭監控 sample。
請用廣東話回答以下問題：
1. 你實際見到咩畫面變化、人物活動、店舖狀況？
2. 你實際聽到咩類型聲音、對話、背景音？
3. 呢種影片格式對巡舖分析夠唔夠用？有咩限制？
4. 如果要做 30 分鐘或 1 小時巡舖摘要，你建議點樣用呢條片？
請直接根據片入面內容答，唔好只講理論。"""


def main():
    if len(sys.argv) < 2:
        print("Usage: analyze_video_with_gemini.py <video_path> [output_path]", file=sys.stderr)
        raise SystemExit(1)

    video_path = Path(sys.argv[1]).expanduser().resolve()
    output_path = Path(sys.argv[2]).expanduser().resolve() if len(sys.argv) >= 3 else None

    if not video_path.exists():
        print(f"Video not found: {video_path}", file=sys.stderr)
        raise SystemExit(1)

    load_dotenv("/home/ubuntu/ai-webcam-intelligence-system/.env")
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("No GEMINI_API_KEY found in .env", file=sys.stderr)
        raise SystemExit(1)

    client = genai.Client(api_key=api_key)
    prompt = os.getenv("HMT_GEMINI_ANALYSIS_PROMPT", DEFAULT_PROMPT)

    print(f"Uploading: {video_path}")
    video_file = client.files.upload(file=str(video_path))
    print(f"Uploaded: {video_file.name}")

    while getattr(video_file, "state", None) == "PROCESSING":
        print("Processing...")
        time.sleep(5)
        video_file = client.files.get(name=video_file.name)

    if getattr(video_file, "state", None) == "FAILED":
        print(f"Video processing failed: {video_file}", file=sys.stderr)
        raise SystemExit(1)

    response = client.models.generate_content(
        model=os.getenv("HMT_GEMINI_MODEL", "gemini-1.5-flash"),
        contents=[video_file, prompt],
    )
    text = getattr(response, "text", "") or ""

    if output_path:
        output_path.write_text(text, encoding="utf-8")
        print(f"Saved: {output_path}")
    else:
        print(text)

    client.files.delete(name=video_file.name)


if __name__ == "__main__":
    main()
