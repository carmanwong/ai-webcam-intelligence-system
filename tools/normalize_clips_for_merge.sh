#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <output_dir> <input1.mp4> [input2.mp4 ...]" >&2
  exit 1
fi

OUTPUT_DIR="$1"
shift

mkdir -p "$OUTPUT_DIR"

for INPUT_PATH in "$@"; do
  if [[ ! -f "$INPUT_PATH" ]]; then
    echo "skip missing: $INPUT_PATH" >&2
    continue
  fi

  BASENAME="$(basename "$INPUT_PATH" .mp4)"
  OUTPUT_PATH="$OUTPUT_DIR/${BASENAME}.normalized.mp4"
  PARTIAL_PATH="$OUTPUT_DIR/${BASENAME}.normalized.partial.mp4"

  echo "normalize: $INPUT_PATH -> $OUTPUT_PATH"
  rm -f "$PARTIAL_PATH"

  ffmpeg -y \
    -i "$INPUT_PATH" \
    -vf "scale=640:-2,fps=10" \
    -c:v libx264 \
    -preset veryfast \
    -crf 30 \
    -maxrate 220k \
    -bufsize 440k \
    -c:a aac \
    -b:a 32k \
    -ac 1 \
    -movflags +faststart \
    "$PARTIAL_PATH"

  mv -f "$PARTIAL_PATH" "$OUTPUT_PATH"
done
