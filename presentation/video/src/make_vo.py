"""Synthesise each narration line with edge-tts (South African English); record durations and word timings."""
import asyncio, json, os, re, subprocess, sys

sys.path.insert(0, r"C:\Users\USER\Desktop\REEFPRINT\.workbench\media-tools")
import edge_tts  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FF = r"C:\Users\USER\Desktop\REEFPRINT\.workbench\media-tools\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
VOICE = sys.argv[1] if len(sys.argv) > 1 else "en-ZA-LukeNeural"
ONLY = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
OUT = os.path.join(HERE, "vo", VOICE)
os.makedirs(OUT, exist_ok=True)


async def synth(key, text):
    mp3 = os.path.join(OUT, key + ".mp3")
    comm = edge_tts.Communicate(text, VOICE, rate="-3%", boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as fh:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                fh.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append([chunk["text"], chunk["offset"] / 1e7, chunk["duration"] / 1e7])
    wav = os.path.join(OUT, key + ".wav")
    subprocess.run([FF, "-v", "error", "-y", "-i", mp3, "-ar", "48000", "-ac", "1", wav], check=True)
    r = subprocess.run([FF, "-i", wav], capture_output=True, text=True).stderr
    d = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r)
    return int(d.group(1)) * 3600 + int(d.group(2)) * 60 + float(d.group(3)), words


async def main():
    lines = json.load(open(os.path.join(HERE, "narration.json"), encoding="utf-8"))
    dpath = os.path.join(OUT, "durations.json")
    wpath = os.path.join(OUT, "words.json")
    res = json.load(open(dpath)) if os.path.exists(dpath) else {}
    allw = json.load(open(wpath)) if os.path.exists(wpath) else {}
    for key, text in lines:
        if ONLY and key not in ONLY:
            continue
        dur, words = await synth(key, text)
        res[key] = round(dur, 3)
        allw[key] = words
        print(key, res[key], len(words), flush=True)
    json.dump(res, open(dpath, "w"), indent=1)
    json.dump(allw, open(wpath, "w"), indent=1)
    print("total", round(sum(res[k] for k, _ in lines), 1))


asyncio.run(main())
