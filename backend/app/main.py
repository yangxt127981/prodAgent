"""商品购买咨询 Agent - FastAPI 后端入口"""
from __future__ import annotations

import os
import uuid
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agent import ConsultantAgent

load_dotenv()

app = FastAPI(title="商品购买咨询 Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("ANTHROPIC_API_KEY", "")
if not api_key:
    print("⚠️  警告: 未设置 ANTHROPIC_API_KEY 环境变量")

agent = ConsultantAgent(api_key=api_key)


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str


@app.get("/api/categories")
def get_categories():
    """获取支持的商品品类列表"""
    return {"categories": agent.get_categories()}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """发送消息并获取 Agent 回复"""
    session_id = req.session_id or str(uuid.uuid4())
    try:
        reply = agent.chat(session_id, req.message)
        return ChatResponse(session_id=session_id, reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reset")
def reset_session(req: ChatRequest):
    """重置对话"""
    if req.session_id:
        agent.reset(req.session_id)
    return {"status": "ok"}


@app.get("/api/health")
def health():
    return {"status": "ok"}
