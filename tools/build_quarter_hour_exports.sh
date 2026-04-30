#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <date_key> <input_dir> <output_dir>" >&2
  exit 1
fi

DATE_KEY="$1"
INPUT_DIR="$2"
OUTPUT_DIR="$3"
HTML_PATH="/home/ubuntu/ai-webcam-intelligence-system/web/exports-quarter.html"

mkdir -p "$OUTPUT_DIR"

mapfile -t CLIPS < <(find -L "$INPUT_DIR" -maxdepth 1 -type f -name "CM234_${DATE_KEY}_*.mp4" ! -name "*.partial.mp4" | sort)

if [[ ${#CLIPS[@]} -lt 3 ]]; then
  echo "Need at least 3 clips to build 15-minute exports." >&2
  exit 1
fi

HTML_ITEMS=""
INDEX=1

for (( i=0; i + 2 < ${#CLIPS[@]}; i+=3 )); do
  FIRST="${CLIPS[$i]}"
  SECOND="${CLIPS[$((i+1))]}"
  THIRD="${CLIPS[$((i+2))]}"

  FIRST_BASE="$(basename "$FIRST" .mp4)"
  THIRD_BASE="$(basename "$THIRD" .mp4)"

  FIRST_STAMP="${FIRST_BASE#CM234_}"
  THIRD_STAMP="${THIRD_BASE#CM234_}"

  OUTPUT_NAME="CM234_q15_clip_${INDEX}_${FIRST_STAMP}_to_${THIRD_STAMP}.mp4"
  EXPORT_NAME="EXPORT_CM234_q15_clip_${INDEX}_${FIRST_STAMP}_to_${THIRD_STAMP}.mp4"
  CONCAT_PATH="$OUTPUT_DIR/${OUTPUT_NAME}.concat.txt"
  OUTPUT_PATH="$OUTPUT_DIR/$OUTPUT_NAME"
  NOTE_PATH="$OUTPUT_DIR/${OUTPUT_NAME%.mp4}.NOTES.txt"

  cat > "$CONCAT_PATH" <<EOF
file '$FIRST'
file '$SECOND'
file '$THIRD'
EOF

  ffmpeg -y -f concat -safe 0 -i "$CONCAT_PATH" -c copy "$OUTPUT_PATH" >/dev/null 2>&1
  ln -sfn "$OUTPUT_PATH" "$INPUT_DIR/$EXPORT_NAME"

  cat > "$NOTE_PATH" <<EOF
Quarter-hour export clip ${INDEX}.
Includes:
- $(basename "$FIRST")
- $(basename "$SECOND")
- $(basename "$THIRD")
EOF

  read -r DURATION_SECONDS SIZE_BYTES < <(
    python3 - <<PY
import json
import subprocess

output = subprocess.check_output([
    "ffprobe",
    "-v", "error",
    "-show_entries", "format=duration,size",
    "-of", "json",
    "$OUTPUT_PATH",
], text=True)
payload = json.loads(output)
duration = payload["format"]["duration"]
size = payload["format"]["size"]
print(duration, size)
PY
  )

  DURATION_MINUTES="$(python3 - <<PY
duration = float("$DURATION_SECONDS")
minutes = int(duration // 60)
seconds = int(round(duration % 60))
print(f"{minutes}m {seconds:02d}s")
PY
)"
  SIZE_MB="$(python3 - <<PY
size_bytes = int("$SIZE_BYTES")
print(f"{size_bytes / 1024 / 1024:.2f} MB")
PY
)"

  HTML_ITEMS+=$'\n'"      <div class=\"card\">
        <div class=\"title\">Q15 Clip ${INDEX}</div>
        <div class=\"meta\">${FIRST_STAMP} 到 ${THIRD_STAMP}｜約 ${DURATION_MINUTES}｜約 ${SIZE_MB}</div>
        <div class=\"row\">
          <a class=\"btn\" href=\"/stream/${EXPORT_NAME}\">Open</a>
          <a class=\"btn secondary\" href=\"/stream/${EXPORT_NAME}\" download>Download</a>
        </div>
      </div>"

  INDEX=$((INDEX + 1))
done

cat > "$HTML_PATH" <<EOF
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HMT 15-Minute Export Links</title>
  <style>
    :root {
      --bg: #f5efe8;
      --card: #ffffff;
      --text: #3f3735;
      --muted: #877972;
      --accent: #7f8c67;
      --border: #e7ddd6;
    }
    body {
      margin: 0;
      font-family: "Inter", "Noto Sans TC", sans-serif;
      background: linear-gradient(180deg, #fbf7f2 0%, #f2ece4 100%);
      color: var(--text);
      padding: 32px 20px 64px;
    }
    .wrap {
      max-width: 980px;
      margin: 0 auto;
    }
    h1 {
      margin: 0 0 10px;
      font-size: 2rem;
    }
    p.lead {
      margin: 0 0 28px;
      color: var(--muted);
      line-height: 1.6;
    }
    .grid {
      display: grid;
      gap: 16px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 18px 18px 16px;
      box-shadow: 0 10px 24px rgba(90, 71, 63, 0.06);
    }
    .title {
      font-size: 1.05rem;
      font-weight: 800;
      margin-bottom: 8px;
    }
    .meta {
      color: var(--muted);
      font-size: 0.92rem;
      margin-bottom: 12px;
      line-height: 1.5;
      word-break: break-word;
    }
    .row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    a.btn {
      text-decoration: none;
      display: inline-block;
      padding: 10px 14px;
      border-radius: 10px;
      border: 1px solid var(--accent);
      color: #fff;
      background: var(--accent);
      font-weight: 700;
    }
    a.btn.secondary {
      background: transparent;
      color: var(--accent);
    }
    code {
      background: #edf2e4;
      border-radius: 6px;
      padding: 1px 6px;
      font-size: 0.9em;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>HMT 15 分鐘匯出頁</h1>
    <p class="lead">
      呢頁係另外一套 <code>quarter-hour</code> 版本，每 3 條 5 分鐘片拼成一條 15 分鐘左右嘅 clip。
      命名同 long clip 分開，方便你逐段 download / upload 去 Gemini。
    </p>
    <div class="grid">${HTML_ITEMS}
    </div>
  </div>
</body>
</html>
EOF
