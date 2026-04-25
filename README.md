# AI Webcam Intelligence System (Multi-Store)

## 🎯 核心構思 (The Vision)
呢個系統旨在為 15 間零售舖頭提供一個「自動化 AI 巡舖解決方案」。系統唔單止係錄影，而係透過 AI (Gemini 1.5 Pro) 24 小時分析舖頭嘅營運狀況。

## 🏗️ 系統架構 (The Architecture)
1. **Network**: 透過 **Tailscale Mesh VPN** 打通每一間舖頭嘅內聯網，Mac 直接訪問 Camera RTSP。
2. **Capture**: 使用 **FFmpeg** 定時（例如每 15 分鐘）抓取 10-30 秒嘅有聲短片。
3. **Storage**: 片段即時上傳至 **Cloudflare R2** (S3-compatible)，實現 15 間舖數據嘅集中化管理。
4. **AI Engine**: **Gemini 1.5 Pro** 讀取 R2 片段，進行多模態（視覺+聽覺）分析。
5. **Output**: 輸出結構化 JSON，用於 Dashboard 顯示「人流、排隊長度、店員服務」等指標。

## 🚀 點解要用 Cloudflare R2？
* **AI 易讀**：提供統一嘅 URL，方便 OpenClaw 或 Gemini 快速檢索。
* **零下載費 (Zero Egress)**：管 15 間舖如果成日下載 4K 片，AWS 會好貴，Cloudflare R2 最慳錢。
* **持久性**：舖頭部 Windows Restart 唔會影響已上傳嘅數據。

## 🛠️ 下一步計劃 (Roadmap)
- [ ] 實現 `R2Uploader` 模組。
- [ ] 整合 Gemini Vision API。
- [ ] 建立自動化定時器 (Cron job)。
- [ ] 擴展至 15 間店鋪配置文件。
