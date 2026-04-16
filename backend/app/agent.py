"""商品购买咨询 Agent - 对话引擎（智能知识库过滤 + 流式输出）"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Generator, List

from openai import OpenAI

from .offer_service import fetch_offer_schedule

# 加载知识库
KB_PATH = Path(__file__).parent / "knowledge_base.json"
with open(KB_PATH, "r", encoding="utf-8") as f:
    KNOWLEDGE_BASE = json.load(f)

CATEGORY_NAMES = list(KNOWLEDGE_BASE.keys())

# 每个品类的识别关键词
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "床垫":     ["床垫", "床", "弹簧", "乳胶", "记忆棉", "睡觉", "睡眠", "睡感"],
    "智能马桶": ["马桶", "坐便器", "厕所", "冲水", "烘干", "坑距", "泡沫盾"],
    "花洒套装": ["花洒", "淋浴", "喷头", "莲蓬头", "热水器", "恒温", "洗澡"],
    "智能门锁": ["门锁", "锁", "指纹", "人脸", "密码锁", "猫眼", "入户"],
    "吸顶灯":   ["吸顶灯", "客厅灯", "卧室灯", "天花板", "顶灯", "吸顶"],
    "台灯":     ["台灯", "书桌灯", "台灯", "读写", "学习灯"],
    "落地护眼灯": ["落地灯", "护眼灯", "落地", "阅读灯", "大路灯"],
}

SYSTEM_PROMPT_TEMPLATE = """\
你是一个专业的家居商品购买咨询顾问。你的任务是通过引导式对话，帮助用户挑选最合适的商品。

## 你可以咨询的品类
{category_list}

## 工作流程
1. **识别需求**：当用户说想买某个品类的商品时，先确认品类。
2. **引导提问**：根据该品类的关键维度，逐步向用户提问（每次只问1-2个问题，不要一次问太多）。问题要通俗易懂，避免过于专业的术语。
3. **给出建议**：当收集到足够信息后，从知识库中筛选最匹配的1-3个产品推荐给用户。推荐时**必须**调用 `get_offer_schedule` 工具获取每款产品的排期信息，并在推荐内容中展示。

## 引导提问策略（按品类）

### 床垫
- 这个床垫是谁用的？（成人/儿童/老人）
- 您的预算大概是多少？
- 您喜欢什么样的睡感？（偏软/适中/偏硬）
- 需要多大尺寸的？（1.2m/1.5m/1.8m）

### 智能马桶
- 您家的水压情况如何？（高层/低层/不确定）
- 您的预算大概是多少？
- 您最看重哪些功能？（自动冲洗烘干/泡沫盾防溅/智能翻盖）
- 家里的坑距是多少？（305mm/400mm/不确定）

### 花洒套装
- 您家用的什么类型的热水器？（燃气/电热水器/其他）
- 您的预算大概是多少？
- 您需要恒温功能吗？
- 是否需要带喷枪（方便清洁浴室）？

### 智能门锁
- 家里有老人或小孩吗？（影响开锁方式选择）
- 您的预算大概是多少？
- 您最看重哪些功能？（人脸识别/摄像头监控/智能家居联动）
- 是否需要双摄猫眼？

### 吸顶灯
- 这是安装在什么房间的？（客厅/卧室）
- 房间面积大概多大？
- 您的预算大概是多少？
- 是否需要支持智能控制（如米家/语音控制）？

### 台灯
- 这个台灯主要用途是什么？（读写护眼/氛围装饰）
- 如果是读写：是否需要入座自动开灯功能？
- 您的预算大概是多少？

### 落地护眼灯
- 主要用于什么场景？（阅读/客厅补光）
- 您的预算大概是多少？
- 是否需要上下分控功能？
- 是否需要自带充电插座？

## 推荐产品时的格式
**推荐 N：[产品名称]**
- 品牌：xxx
- 价格段：xxx
- 核心亮点：xxx
- 推荐理由：xxx（结合用户需求说明）
- 📅 直播排期：[调用 get_offer_schedule 获取]

## 注意事项
- 语气亲切自然，像朋友聊天一样
- 如果用户问的品类不在知识库中，礼貌地告知目前支持的品类
- 不要编造知识库中没有的产品信息
- 引导提问时使用通俗语言，必要时解释专业概念

## 当前相关产品知识库
{knowledge_json}
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_offer_schedule",
            "description": "根据商品的 Offer 单号查询该商品的直播排期信息，包括直播日期、直播间、场次、销售状态等。推荐产品时必须调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "offer_code": {
                        "type": "string",
                        "description": "商品的 Offer 单号，例如 OSPU202509020699",
                    }
                },
                "required": ["offer_code"],
            },
        },
    }
]


def _detect_categories(texts: list[str]) -> dict:
    """根据文本列表检测相关品类，返回过滤后的知识库"""
    combined = " ".join(texts)
    matched = {
        cat: KNOWLEDGE_BASE[cat]
        for cat, keywords in CATEGORY_KEYWORDS.items()
        if any(kw in combined for kw in keywords)
    }
    return matched if matched else KNOWLEDGE_BASE


def _build_system_prompt(kb: dict) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        category_list=", ".join(CATEGORY_NAMES),
        knowledge_json=json.dumps(kb, ensure_ascii=False),
    )


class ConsultantAgent:
    def __init__(self, api_key: str, base_url: str, model: str, offer_api_token: str = ""):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.offer_api_token = offer_api_token
        self.conversations: Dict[str, List[dict]] = {}

    def _run_tool(self, tool_name: str, tool_args: dict) -> str:
        if tool_name == "get_offer_schedule":
            return fetch_offer_schedule(tool_args["offer_code"], self.offer_api_token)
        return "未知工具"

    def _get_messages(self, session_id: str, user_message: str) -> list[dict]:
        """构建消息列表，附带智能过滤后的知识库"""
        history = self.conversations.get(session_id, [])
        all_texts = [user_message] + [m["content"] for m in history if isinstance(m.get("content"), str)]
        kb = _detect_categories(all_texts)
        system = _build_system_prompt(kb)
        return [{"role": "system", "content": system}] + history

    # ── 流式接口（供 SSE 使用）────────────────────────────────────────────
    def chat_stream(self, session_id: str, user_message: str) -> Generator[dict, None, None]:
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        self.conversations[session_id].append({"role": "user", "content": user_message})
        messages = self._get_messages(session_id, user_message)

        full_reply = ""

        for _ in range(5):  # 最多 5 轮 tool call
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                stream=True,
            )

            # 收集 tool calls 和 content
            tool_calls_buf: dict[int, dict] = {}
            chunk_content = ""

            for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta
                if delta.content:
                    chunk_content += delta.content
                    full_reply += delta.content
                    yield {"type": "token", "content": delta.content}

                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_buf:
                            tool_calls_buf[idx] = {"id": tc.id or "", "name": "", "arguments": ""}
                        if tc.id:
                            tool_calls_buf[idx]["id"] = tc.id
                        if tc.function.name:
                            tool_calls_buf[idx]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_calls_buf[idx]["arguments"] += tc.function.arguments

            # 没有 tool call，结束
            if not tool_calls_buf:
                break

            # 通知前端正在查询排期
            yield {"type": "tool_start", "message": "正在查询产品排期信息..."}

            # 把 assistant tool_call 消息加入 messages
            messages.append({
                "role": "assistant",
                "content": chunk_content or None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]},
                    }
                    for tc in tool_calls_buf.values()
                ],
            })

            # 执行工具并追加结果
            for tc in tool_calls_buf.values():
                args = json.loads(tc["arguments"])
                result = self._run_tool(tc["name"], args)
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})

        self.conversations[session_id].append({"role": "assistant", "content": full_reply})
        yield {"type": "done"}

    # ── 非流式接口（兼容保留）────────────────────────────────────────────
    def chat(self, session_id: str, user_message: str) -> str:
        reply = ""
        for event in self.chat_stream(session_id, user_message):
            if event["type"] == "token":
                reply += event["content"]
        return reply

    def reset(self, session_id: str):
        self.conversations.pop(session_id, None)

    def get_categories(self) -> list[str]:
        return CATEGORY_NAMES
