import os, requests, json, subprocess
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")
VOICE_ID = "你的ElevenLabs聲音ID"  # 選好男聲後填入

# ── 1. 讀取腳本 ──────────────────────────────
with open("script.txt", "r", encoding="utf-8") as f:
    script = f.read()

# ── 2. ElevenLabs 生成旁白 ───────────────────
client = ElevenLabs(api_key=ELEVENLABS_KEY)
audio = client.text_to_speech.convert(
    voice_id=VOICE_ID,
    text=script,
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128"
)
with open("output/narration.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)
print("✅ 旁白生成完成")

# ── 3. Pexels 抓 B-roll ──────────────────────
def fetch_broll(keyword, count=3):
    headers = {"Authorization": PEXELS_KEY}
    r = requests.get(
        f"https://api.pexels.com/videos/search",
        headers=headers,
        params={"query": keyword, "per_page": count, "orientation": "portrait"}
    )
    videos = r.json().get("videos", [])
    paths = []
    for i, v in enumerate(videos):
        # 抓最高畫質的 portrait 版本
        files = sorted(v["video_files"], key=lambda x: x.get("width", 0))
        url = files[-1]["link"]
        path = f"output/broll_{i}.mp4"
        with open(path, "wb") as f:
            f.write(requests.get(url).content)
        paths.append(path)
    return paths

# 從腳本關鍵字決定搜尋詞（可讓 Claude Code 自動判斷）
broll_paths = fetch_broll("couple romantic", count=3)
print(f"✅ B-roll 下載完成：{len(broll_paths)} 支")

# ── 4. ffmpeg 合成 9:16 ──────────────────────
# 把 B-roll 串接
with open("output/broll_list.txt", "w") as f:
    for p in broll_paths:
        f.write(f"file '{os.path.abspath(p)}'\n")

subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", "output/broll_list.txt",
    "-i", "output/narration.mp3",
    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
    "-c:v", "libx264", "-c:a", "aac",
    "-shortest",
    "output/final.mp4"
], check=True)
print("✅ 影片合成完成：output/final.mp4")