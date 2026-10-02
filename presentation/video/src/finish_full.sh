#!/usr/bin/env bash
# Join the rendered segments losslessly, check the frame count, and mux the soundtrack.
set -e
cd "C:/Users/USER/AppData/Local/Temp/claude/C--Users-USER-Desktop-REEFPRINT/ad003297-3f40-4fce-8044-df292eebbd73/scratchpad/out"
FF="C:/Users/USER/Desktop/REEFPRINT/.workbench/media-tools/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"
DEST="C:/Users/USER/Desktop/REEFPRINT/presentation/video"
printf "file 'part0.mp4'\nfile 'partA.mp4'\nfile 'partB.mp4'\nfile 'part1.mp4'\nfile 'partC.mp4'\n" > concat.txt
for f in part0 partA partB part1 partC; do
  n=$("$FF" -v error -i $f.mp4 -map 0:v:0 -c copy -f null - -stats 2>&1 | tr '\r' '\n' | grep -o 'frame= *[0-9]*' | tail -1 | grep -o '[0-9]*')
  echo "$f frames=$n"
done
"$FF" -v error -y -f concat -safe 0 -i concat.txt -c copy video_full_silent.mp4
n=$("$FF" -v error -i video_full_silent.mp4 -map 0:v:0 -c copy -f null - -stats 2>&1 | tr '\r' '\n' | grep -o 'frame= *[0-9]*' | tail -1 | grep -o '[0-9]*')
echo "joined frames=$n (expected 6726)"
"$FF" -v error -y -i video_full_silent.mp4 -i audio.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$DEST/REEFPRINT-promo-full.mp4"
ls -la "$DEST/REEFPRINT-promo-full.mp4"
