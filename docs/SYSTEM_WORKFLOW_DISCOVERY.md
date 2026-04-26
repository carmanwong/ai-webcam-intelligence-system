# HMT AI 巡舖系統：系統運作與技術發現 (2026-04-26 更新)

## 🏆 最終成功架構 (Current Success)

### 1. 畫質與串流優化 (4K Upgrade)
- **串流選擇**: 已由 `_sub` (低畫質) 升級至 **`_main` (高畫質)**。
- **解析度**: 3840x2160 (4K HEVC)，提供極清晰嘅肢體動作同貨品細節。
- **錄影模式**: 無間斷錄影，每 **5 分鐘** 切割成一個檔案。
- **檔案體積**: 5 分鐘 4K 影片約 **70MB - 150MB**。部機 200GB 空間足以支持 3 日以上嘅全天候紀錄。

### 2. 營運自動化 (Automation)
- **營業時間**: 已調整為 **08:00 - 22:45**，覆蓋完整開舖與收舖過程。
- **AI 巡舖頻率**: 每 **15 分鐘** 自動揀選最新嘅 5 分鐘片段交畀 Gemini 1.5 Flash 分析。
- **音訊分析**: 錄影包含原始音軌，AI 會同時聽取店內對話，判斷服務質素。

### 3. HMT 影片巡視廳 (Video Gallery Web App)
- **功能**: 建立咗一個專屬 Web App 擺喺 Port **4319**。
- **用途**: 老闆可以喺 MacBook 透過 Tailscale 直接瀏覽、播放最近 3 日嘅所有 5 分鐘片段。
- **安全**: 僅限 Tailscale 內網連線，確保影片私隱。

---

## 🛠️ 技術修正紀錄
- **Timeout 優化**: 針對 4K 大檔案，將 FFmpeg 儲存超時時間由 60s 增加到 **120s**，解決大檔案儲存失敗問題。
- **Module 隔離**: 修正咗 `main.py` 嘅結構，確保 `lookout.py` 導入時唔會發生衝突。
- **網絡穿透**: 持續使用內網 IP `192.168.1.113` 進行連線，證明 Subnet Routing 係最穩定方案。

## 🚀 啟動指令
```bash
# 啟動錄影與 AI 分析
cd /home/ubuntu/ai-webcam-intelligence-system
nohup python3 -u lookout.py >> lookout.log 2>&1 &

# 啟動影片巡視廳
cd /home/ubuntu/ai-webcam-intelligence-system/web
nohup node server.js > gallery.log 2>&1 &
```
