import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from google import genai
from google.genai import types
from conversation_store import ConversationStore

app = Flask(__name__)

line_config = Configuration(access_token=os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])
gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
store = ConversationStore()

SYSTEM_PROMPT = """使用者是歐拉蔬食的經營者，居住在台灣高雄三民區，擔任私人導遊助理角色。

【飲食原則（所有餐廳推薦必須遵守）】
- 素食，可接受蛋、奶、起司
- 嚴禁任何肉品（含海鮮）
- 嚴禁五辛：蔥、蒜、韭、蕎、興渠
- 嚴禁酒精飲品
- 絕對排除食材：青椒、茄子、彩椒、四季豆、扁豆、芹菜
- 優先推薦低消費場所（台幣 150 元以下）

【導遊功能】
1. 行程規劃：依目的地、日期、喜好安排景點與動線
2. 餐廳推薦：嚴格過濾符合飲食規則的素食餐廳
3. 交通建議：高雄在地交通優先（捷運、公車、YouBike）
4. 景點介紹：附實用資訊（開放時間、票價、特色）
5. 預算估算：依需求提供花費試算

【回覆規則】
- 使用繁體中文
- 禁止使用第一人稱（我、我的）與第二人稱（你、你的），以「使用者」或中性稱呼代替
- 輸出結構化、分段清晰
- 資訊不確定時誠實說明，建議查詢官方來源確認
- 以高雄為主場，熟悉在地資源

【開場白範例】
當使用者詢問旅遊規劃時，先確認：目的地、出發日期、天數、同行人數，再提供完整建議。"""


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text.strip()

    if user_text in ["/清除", "/reset", "清除對話"]:
        store.clear(user_id)
        _reply(event.reply_token, "對話記錄已清除，可重新開始規劃行程。")
        return

    if user_text in ["/說明", "/help", "使用說明"]:
        reply = (
            "🗺️ 私人導遊助理使用說明\n\n"
            "【可詢問的內容】\n"
            "• 景點推薦與介紹\n"
            "• 素食餐廳搜尋（符合個人飲食規則）\n"
            "• 行程規劃（請告知目的地、日期、天數）\n"
            "• 交通建議與路線\n"
            "• 預算估算\n\n"
            "【指令】\n"
            "/清除 — 清除對話記錄\n"
            "/說明 — 顯示此說明\n\n"
            "直接輸入問題即可開始！"
        )
        _reply(event.reply_token, reply)
        return

    history = store.get(user_id)

    # 組成 Gemini 格式的對話歷史
    gemini_history = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    try:
        contents = []
        for msg in gemini_history:
            contents.append(types.Content(
                role=msg["role"],
                parts=[types.Part(text=msg["parts"][0])]
            ))
        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=user_text)]
        ))
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        )
        assistant_text = response.text
    except Exception as e:
        assistant_text = f"系統發生錯誤，請稍後再試。（{type(e).__name__}）"

    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": assistant_text})
    store.set(user_id, history[-20:])

    _reply(event.reply_token, assistant_text)


def _reply(reply_token: str, text: str):
    if len(text) > 4500:
        text = text[:4497] + "…"
    with ApiClient(line_config) as api_client:
        api = MessagingApi(api_client)
        api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=text)],
            )
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
