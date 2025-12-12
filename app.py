
import os
import json
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="AI Learning Advisor Agent", page_icon="🎓", layout="centered")

APP_TITLE = "AI Learning Advisor Agent"
APP_DESC = "一個任務導向的學習輔導 Agent：會主動追問背景 → 分析 → 給出結構化建議。"

SYSTEM_PROMPT = """
你是一個學習輔導 Agent（Learning Advisor Agent），專長是協助大學生釐清學習困難、
規劃學習策略並提供可執行的建議。

規則：
1) 先詢問背景（課程、程度、困難、可用時間）
2) 資訊不足先追問
3) 資訊足夠後輸出：問題診斷、學習策略、行動清單、推薦資源
"""

MODEL_DEFAULT = "gpt-4.1-mini"

st.sidebar.title("設定")
api_key = st.sidebar.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
model = st.sidebar.text_input("Model", value=MODEL_DEFAULT)

if st.sidebar.button("清空對話"):
    st.session_state.pop("messages", None)
    st.rerun()

st.title(APP_TITLE)
st.caption(APP_DESC)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "你好！請先告訴我你目前在學什麼，以及最大的學習困難是什麼？"}
    ]

for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_text = st.chat_input("輸入你的學習狀況…")

def mock_agent_reply(messages):
    # 取最後一個 user 內容
    last_user = ""
    for m in reversed(messages):
        if m["role"] == "user":
            last_user = m["content"]
            break

    # 簡單規則：資訊不足就追問；足夠就給結構化建議
    keywords = ["課", "程度", "卡", "時間", "目標", "考試", "作業", "期末", "報告", "專題"]
    hit = sum(1 for k in keywords if k in last_user)
    need_more = (hit < 2 and len(last_user) < 40)

    if need_more:
        return (
            "（離線 Demo 模式）我先了解一下你的狀況，幫你做出可執行計畫：\n"
            "1) 你是什麼科目/課程？（例：ML、OS、線代）\n"
            "2) 你目前程度到哪？（看過哪些章節/作業做得出來嗎）\n"
            "3) 最卡的是哪一塊？（觀念/推導/寫程式/題目）\n"
            "4) 一週可投入幾小時？最近有沒有 deadline？"
        )

    return (
        "（離線 Demo 模式）\n\n"
        "## 問題診斷\n"
        "- 你目前描述的卡點偏向：概念理解 + 練習量不足（若不準你再修正）\n\n"
        "## 學習策略\n"
        "**短期（3天）**\n"
        "- 每天 45–60 分鐘：看 1 個核心概念 + 做 3 題對應練習\n"
        "- 錯題要寫『錯因』：看不懂題意 / 不會套公式 / 推導卡住 / 程式實作卡住\n\n"
        "**中期（2週）**\n"
        "- 每週做一次小測：10 題，限時，檢查弱點\n"
        "- 以『題型』整理筆記，而不是只抄章節\n\n"
        "## 每日/每週行動清單\n"
        "- Day1：列出必會清單（5–10項）\n"
        "- Day2：針對最弱 2 項各做 5 題\n"
        "- Day3：做一回合小測 + 回補錯題\n"
        "- Weekly：固定 2 次 90 分鐘深度練習（關掉手機）\n\n"
        "## 推薦資源\n"
        "- 關鍵字：\"practice problems\" + 你的課名\n"
        "- 練習方式：先看例題→遮答案自己做→對答案→寫下錯因\n"
    )

def call_llm(messages):
    # 沒填 API Key 就直接離線（方便 demo）
    if not api_key:
        return mock_agent_reply(messages)

    client = OpenAI(api_key=api_key)
    try:
        resp = client.responses.create(
            model=model,
            input=messages,
        )
        return resp.output_text
    except Exception as e:
        # 額度不足 / 429 → 自動退回離線，demo 不會死
        err = str(e)
        if "insufficient_quota" in err or "RateLimitError" in err or "429" in err:
            return "（目前 API 額度不足，已自動切換離線 Demo 模式）\n\n" + mock_agent_reply(messages)
        raise


if user_text:
    if not api_key:
        st.error("請先輸入 API Key")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        reply = call_llm(st.session_state.messages)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

st.markdown("---")
chat_json = json.dumps(st.session_state.messages, ensure_ascii=False, indent=2)
st.download_button("下載聊天紀錄 JSON", chat_json, "chat_log.json", "application/json")
