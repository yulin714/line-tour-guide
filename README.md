# 私人導遊 Line Bot

## 快速啟動

### 1. 安裝套件
```bash
cd line-tour-guide
pip install -r requirements.txt
```

### 2. 設定環境變數
```bash
cp .env.example .env
# 編輯 .env，填入三組金鑰
```

### 3. 本機測試（需安裝 ngrok）
```bash
# 終端機 A：啟動伺服器
python app.py

# 終端機 B：建立公開網址
ngrok http 5000
```

將 ngrok 產生的 HTTPS 網址貼到 Line Developers Console：
Webhook URL = `https://xxxx.ngrok.io/callback`

### 4. 正式部署（Zeabur / Railway / Render）
將資料夾上傳，設定環境變數，部署即可。

---

## 取得金鑰

| 金鑰 | 位置 |
|------|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | Line Developers → Messaging API → Channel access token |
| `LINE_CHANNEL_SECRET` | Line Developers → Basic settings → Channel secret |
| `ANTHROPIC_API_KEY` | console.anthropic.com |

---

## Bot 功能

| 指令 / 輸入 | 功能 |
|------------|------|
| 自然語言問題 | Claude 回覆，記憶對話上下文 |
| `/清除` | 清除此用戶的對話記錄 |
| `/說明` | 顯示使用說明 |

## 內建規則（自動套用，無需每次說明）
- 純素食，可蛋奶，無五辛、無酒精
- 排除：青椒、茄子、彩椒、四季豆、扁豆、芹菜
- 優先推薦 NT$150 以下場所
- 以高雄為主場
