import os, requests, subprocess
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")
VOICE_ID = "Z9RJEkFYQw307BCQULDR"

os.makedirs("output", exist_ok=True)

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
        "https://api.pexels.com/videos/search",
        headers=headers,
        params={"query": keyword, "per_page": count, "orientation": "portrait"}
    )
    videos = r.json().get("videos", [])
    paths = []
    for i, v in enumerate(videos):
        files = sorted(v["video_files"], key=lambda x: x.get("width", 0))
        url = files[-1]["link"]
        path = f"output/broll_{i}.mp4"
        with open(path, "wb") as f:
            f.write(requests.get(url).content)
        paths.append(path)
    return paths

broll_paths = fetch_broll("couple romantic", count=3)
print(f"✅ B-roll 下載完成：{len(broll_paths)} 支")

# ── 4. 生成 SRT 字幕 ─────────────────────────
def build_srt(text, audio_path):
    """用 ffprobe 取得音頻長度，依行數平均分配時間軸"""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True
    )
    total_sec = float(result.stdout.strip())

    # 每行最多 15 個中文字
    lines = []
    buf = ""
    for ch in text:
        buf += ch
        if ch in ("。", "！", "？", "，", "、") or len(buf) >= 15:
            lines.append(buf.strip())
            buf = ""
    if buf.strip():
        lines.append(buf.strip())

    seg = total_sec / len(lines) if lines else total_sec

    def fmt(s):
        h = int(s // 3600)
        m = int((s % 3600) // 60)
        sec = s % 60
        return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")

    srt = ""
    for i, line in enumerate(lines):
        start = i * seg
        end = (i + 1) * seg
        srt += f"{i+1}\n{fmt(start)} --> {fmt(end)}\n{line}\n\n"

    srt_path = "output/subtitles.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt)
    return srt_path

srt_path = build_srt(script, "output/narration.mp3")
print("✅ 字幕生成完成")

# ── 5. ffmpeg 合成 9:16 + 燒入字幕 ───────────
with open("output/broll_list.txt", "w") as f:
    for p in broll_paths:
        f.write(f"file '{os.path.abspath(p)}'\n")

subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", "output/broll_list.txt",
    "-i", "output/narration.mp3",
    "-vf", (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        f"subtitles={srt_path}:force_style="
        "'FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,Outline=3,Bold=1,"
        "Alignment=2,MarginV=200'"
    ),
    "-c:v", "libx264", "-c:a", "aac",
    "-shortest",
    "output/final.mp4"
], check=True)
print("✅ 影片合成完成：output/final.mp4")
