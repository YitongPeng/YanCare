"""
AI咨询路由 - DeepSeek集成
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.ai import AIService
from app.services.auth import AuthService

router = APIRouter(prefix="/ai", tags=["AI咨询"])


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # "user" 或 "assistant"
    content: str


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    history: List[ChatMessage] = []  # 历史对话


class ChatResponse(BaseModel):
    """聊天响应"""
    reply: str
    

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(AuthService.get_current_user)
):
    """
    AI咨询对话
    
    使用DeepSeek API进行养发相关的智能问答
    """
    ai_service = AIService()
    reply = await ai_service.chat(
        message=request.message,
        history=request.history,
        user_id=current_user.id
    )
    return ChatResponse(reply=reply)


@router.get("/suggestions")
async def get_suggestions():
    """
    获取推荐问题
    
    返回一些常见的养发相关问题，供用户快捷选择
    """
    return {
        "suggestions": [
            "脱发怎么办",
            "你们有什么卡",
            "脱发用什么卡",
            "怎么预约",
        ]
    }
