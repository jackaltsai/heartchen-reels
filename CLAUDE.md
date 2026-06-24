# 心辰短影音自動化專案

## 專案目標
將文字腳本自動轉成 Instagram Reels 格式影片（9:16, 1080x1920）

## 輸入
- `script.txt`：旁白腳本（繁體中文）
- 角色設定：溫柔男友語氣（心辰品牌）

## 輸出
- `output/final.mp4`：完成品，可直接上傳 IG

## 工具鏈
1. ElevenLabs API → 生成旁白 mp3
2. Pexels API → 抓 B-roll 影片
3. ffmpeg → 合成、加字幕、輸出 9:16

## 環境變數
從 .env 讀取 ELEVENLABS_API_KEY、PEXELS_API_KEY

## 字幕風格
- 字體：白色粗體，黑色描邊
- 位置：畫面下方 1/3
- 每行不超過 15 個中文字