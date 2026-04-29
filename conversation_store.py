import json
import os


class ConversationStore:
    """以 JSON 檔案儲存各用戶的對話歷史（輕量本地方案）。"""

    def __init__(self, path: str = "conversations.json"):
        self.path = path
        self._data: dict = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self._data = json.load(f)

    def get(self, user_id: str) -> list:
        return list(self._data.get(user_id, []))

    def set(self, user_id: str, history: list):
        self._data[user_id] = history
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def clear(self, user_id: str):
        self._data.pop(user_id, None)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
