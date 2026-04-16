"""商品购买咨询 Agent - FastAPI 后端入口"""
from __future__ import annotations

import json
import os
import uuid
from typing import AsyncGenerator, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .agent import ConsultantAgent

load_dotenv()

app = FastAPI(title="商品购买咨询 Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("LLM_API_KEY", "")
base_url = os.getenv("LLM_BASE_URL", "")
model = os.getenv("LLM_MODEL", "qwen-max")
offer_api_token = os.getenv("OFFER_API_TOKEN", "")
if not api_key:
    print("⚠️  警告: 未设置 LLM_API_KEY 环境变量")
if not offer_api_token:
    print("⚠️  警告: 未设置 OFFER_API_TOKEN，排期功能不可用")

agent = ConsultantAgent(api_key=api_key, base_url=base_url, model=model, offer_api_token=offer_api_token)


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str


@app.get("/api/categories")
def get_categories():
    return {"categories": agent.get_categories()}


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """流式接口，SSE 格式返回"""
    session_id = req.session_id or str(uuid.uuid4())

    async def generate() -> AsyncGenerator[str, None]:
        # 先推送 session_id
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id}, ensure_ascii=False)}\n\n"
        try:
            for event in agent.chat_stream(session_id, req.message):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """非流式接口（兼容保留）"""
    session_id = req.session_id or str(uuid.uuid4())
    try:
        reply = agent.chat(session_id, req.message)
        return ChatResponse(session_id=session_id, reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reset")
def reset_session(req: ChatRequest):
    if req.session_id:
        agent.reset(req.session_id)
    return {"status": "ok"}


@app.get("/api/health")
def health():
    return {"status": "ok"}
