#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <output_path.mp4> <input1.mp4> [input2.mp4 ...]" >&2
  exit 1
fi

OUTPUT_PATH="$1"
shift

WORK_DIR="$(dirname "$OUTPUT_PATH")"
mkdir -p "$WORK_DIR"

CONCAT_PATH="$(mktemp)"
trap 'rm -f "$CONCAT_PATH"' EXIT

for INPUT_PATH in "$@"; do
  if [[ ! -f "$INPUT_PATH" ]]; then
    echo "Missing input: $INPUT_PATH" >&2
    exit 1
  fi
  printf "file '%s'\n" "$INPUT_PATH" >> "$CONCAT_PATH"
done

PARTIAL_PATH="${OUTPUT_PATH%.mp4}.partial.mp4"
rm -f "$PARTIAL_PATH"

ffmpeg -y \
  -f concat -safe 0 -i "$CONCAT_PATH" \
  -vf "fps=1" \
  -c:v libx264 \
  -preset veryfast \
  -crf 30 \
  -pix_fmt yuv420p \
  -c:a copy \
  -movflags +faststart \
  "$PARTIAL_PATH"

mv -f "$PARTIAL_PATH" "$OUTPUT_PATH"
