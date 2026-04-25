# Strategy: Integrating 100+ Xiaomi Cameras via Custom Firmware

## 🎯 項目背景 (Context)
公司目前擁有超過 100 粒 2025 年前購入的小米系列攝錄機。目前主要問題在於「大陸帳戶+香港使用」導致的速度極慢，且無法被 AI 自動化讀取數據。

## 🏴‍☠️ 解放計劃 (The Hack Plan)
旨在透過「刷機 (Firmware Hack)」打破小米的雲端封鎖，開啟 RTSP 協議，實現 100% 本地化控制。

### 1. 核心步驟 (The SOP)
- **型號審計**：確認底座 Model Number (例如 MJSXJ05CM, ISC5)。
- **刷機媒介**：使用 32GB FAT32 MicroSD 卡。
- **目標固件**：使用 GitHub 開源項目 (如 yi-hack-v5, Dafang-Hacks)。
- **結果**：獲得標準 RTSP URL (`rtsp://[IP]:8554/unicast`)。

### 2. 網絡集成 (Tailscale Bridge)
- **子網路由**：小米 Cam 不直接安裝 Tailscale，而是透過店鋪內的 Windows POS 機作為 **Subnet Router** 轉發流量。
- **安全性**：刷機後可在 Router 端斷絕小米 Cam 連接外網，防止數據回流北京伺服器。

---

## 🏗️ 指揮中心升級 (Server Roadmap)

### 1. 核心伺服器：Mac Studio M2 Max
- **預算**：約 $15,000 HKD (Refurbished/Used)。
- **配置**：64GB Unified Memory (用於多路 AI 並行分析)。
- **散熱**：支持 24/7 不間斷高負載運作。

### 2. 儲存架構：Hybrid Storage
- **Local HDD (倉庫)**：外接 20TB+ 企業級硬碟櫃。負責儲存 15 間舖的 24 小時全高清 (2K/4K) 原始片段。
- **Cloudflare R2 (AI 閱覽室)**：僅儲存 AI 篩選後的「10秒 精華 Snippet」。
- **預算控制**：將雲端儲存費控制在 $100-$200 HKD/月 以內。

---

## 🤖 AI 智能調度邏輯
- **Motion-Triggered Harvest**：平時不錄影，由 Python Bot 監聽動態，發現有人郁才啟動 2K 錄影並推送 R2。
- **Automatic Refill**：若發生網絡斷線，Bot 會在恢復後自動透過 HTTP API 從 SD 卡中「打撈」缺失的片段並同步至 R2。

## 🛠️ 下一步行動 (Action Items)
1. [ ] 拍攝小米 Cam 機底標籤，確認刷機型號。
2. [ ] 準備 32GB 測試用 SD 卡。
3. [ ] 喺 main.py 加入 `XiaomiRTSP` 支持模組。
