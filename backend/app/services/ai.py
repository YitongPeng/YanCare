"""
AI咨询服务 - DeepSeek + 混合检索 + 意图分类
"""
from typing import List, Optional
import httpx
import re

from app.config import settings
from app.services.rag_hybrid import hybrid_rag_service
from app.services.intent_classifier import intent_classifier


# 系统提示词
SYSTEM_PROMPT = """你是"燕儿"，燕斛堂养发馆的智能养护顾问。

【你的身份】
- 你是一位亲切、专业的养发顾问
- 你不是医生，不提供医疗建议
- 涉及严重健康问题时，建议用户就医

【回答规则】
1. 语气亲切自然，像朋友聊天
2. 回答简洁明了，不要太长（100-200字为宜）
3. 基于提供的知识库内容回答，不要编造
4. 可以适当引导用户了解我们的服务，但不要太商业化
5. 回答后可以反问一个相关问题，引导对话
6. 如果知识库没有相关内容，诚实说不清楚，建议到店咨询
7. **重要：请返回纯文本，不要使用 Markdown 格式符号（如 **、*、[]() 等）**

【门店信息】
- 燕斛堂养发（水岸新都店）
- 燕斛堂养发（阳光国际店）
- 营业时间：8:15 - 20:30
"""


class AIService:
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_url = settings.DEEPSEEK_API_URL
    
    async def chat(
        self, 
        message: str, 
        history: List[dict] = None,
        user_id: Optional[int] = None
    ) -> str:
        """
        AI对话（意图分类 + 混合检索 + RAG）
        """
        # 1. 意图分类
        intent, confidence = intent_classifier.classify(message)
        print(f"🎯 意图: {intent} (置信度: {confidence:.2f})")
        
        # 2. 根据意图决定是否需要检索知识库
        relevant_docs = []
        
        if intent_classifier.is_need_rag(intent):
            # 获取意图对应的类别（用于针对性检索）
            category = intent_classifier.get_intent_category(intent)
            print(f"📚 检索类别: {category}")
            
            # 混合检索（养发知识类多返回一些，确保内容完整）
            n_docs = 8 if intent == intent_classifier.INTENT_CONSULT_KNOWLEDGE else 5
            relevant_docs = hybrid_rag_service.search(
                message, 
                n_results=n_docs,
                intent_category=category,
                use_reranking=True
            )
            print(f"📄 检索到 {len(relevant_docs)} 个相关文档")
        
        # 3. 如果有 API Key，尝试调用 DeepSeek
        if self.api_key:
            # 构建知识上下文（养发知识类用更多文档）
            knowledge_context = ""
            if relevant_docs:
                knowledge_context = "\n\n【相关知识】\n"
                # 养发知识用5个，其他用3个
                max_docs = 5 if intent == intent_classifier.INTENT_CONSULT_KNOWLEDGE else 3
                for i, doc in enumerate(relevant_docs[:max_docs], 1):
                    knowledge_context += f"{i}. {doc['content']}\n\n"
            
            full_system_prompt = SYSTEM_PROMPT + knowledge_context
            result = await self._call_deepseek(full_system_prompt, message, history)
            
            # 如果 API 调用成功，进行后处理
            if result and not result.startswith("抱歉"):
                # 后处理：清理 Markdown + 添加 ACTION 标记
                result = self._post_process_reply(result, intent)
                return result
        
        # 4. API 不可用或调用失败，使用本地智能回复
        return self._smart_reply(message, intent, relevant_docs)
    
    async def _call_deepseek(
        self, 
        system_prompt: str, 
        message: str, 
        history: List = None
    ) -> str:
        """调用 DeepSeek API"""
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史消息
        if history:
            for msg in history[-10:]:
                # 兼容 dict 和 Pydantic 对象
                if hasattr(msg, 'role'):
                    messages.append({"role": msg.role, "content": msg.content})
                else:
                    messages.append({"role": msg["role"], "content": msg["content"]})
        
        # 添加当前消息
        messages.append({"role": "user", "content": message})
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return "抱歉，AI服务暂时不可用，请稍后再试。"
                    
        except Exception as e:
            print(f"DeepSeek API 错误: {e}")
            return "抱歉，服务出现问题，请稍后再试。"
    
    def _smart_reply(self, message: str, intent: str, docs: List[dict]) -> str:
        """
        本地智能回复（基于意图 + RAG检索结果）
        """
        # 1. 处理问候语
        if intent == intent_classifier.INTENT_GREETING:
            return """您好！我是燕儿，燕斛堂的智能养护顾问 😊

您可以问我：
• 脱发怎么办
• 你们有什么卡
• 脱发用什么卡
• 怎么预约

请问有什么可以帮您的吗？"""
        
        # 2. 处理感谢
        if intent == intent_classifier.INTENT_THANKS:
            return "不客气！很高兴能帮到您 😊\n\n如果还有其他问题，随时问我哦！"
        
        # 3. 处理再见
        if intent == intent_classifier.INTENT_GOODBYE:
            return "再见！期待您的光临 👋\n\n燕斛堂祝您头发健康、生活愉快！"
        
        # 3.5 处理预约咨询 - 添加跳转标记
        if intent == intent_classifier.INTENT_CONSULT_BOOKING:
            # 在回答末尾添加特殊标记，前端会识别并显示按钮
            response = self._build_booking_response(docs)
            return response + "\n\n[ACTION:GOTO_BOOKING]"
        
        # 4. 处理投诉反馈
        if intent == intent_classifier.INTENT_COMPLAINT:
            return """非常抱歉给您带来不好的体验 🙏

您的反馈对我们非常重要。建议您：
1. 拨打门店电话：86281118
2. 直接到店与店长沟通

我们会认真对待每一条反馈，不断改进服务！"""
        
        # 5. 咨询类问题 - 基于检索结果回答
        if not docs:
            category_tips = {
                intent_classifier.INTENT_CONSULT_CARD: "您可以问：有什么卡？办卡多少钱？",
                intent_classifier.INTENT_CONSULT_SERVICE: "您可以问：有什么服务？泡头是什么？",
                intent_classifier.INTENT_CONSULT_BOOKING: "您可以问：怎么预约？可以取消吗？",
                intent_classifier.INTENT_CONSULT_STORE: "您可以问：门店地址在哪？营业时间？",
                intent_classifier.INTENT_CONSULT_KNOWLEDGE: "您可以问：脱发怎么办？养发多久做一次？",
            }
            
            tip = category_tips.get(intent, "您可以换个方式问问")
            
            return f"""抱歉，我暂时找不到相关信息。

{tip}

或者拨打电话咨询：86281118"""
        
        # 对于养发知识类问题，合并多个文档以提供更完整的答案
        if intent == intent_classifier.INTENT_CONSULT_KNOWLEDGE and len(docs) > 1:
            # 合并前3个最相关的文档
            combined_content = ""
            for i, doc in enumerate(docs[:3]):
                content = doc["content"]
                # 去重：如果内容重复度高，跳过
                if i > 0 and content in combined_content:
                    continue
                combined_content += content + "\n\n"
            
            return f"{combined_content.strip()}\n\n💡 以上建议希望对您有帮助。如需针对性方案，欢迎到店咨询我们的理疗师。"
        
        # 获取最相关的文档
        best_doc = docs[0]
        content = best_doc["content"]
        category = best_doc.get("metadata", {}).get("category", "")
        
        # 如果是FAQ格式（问：xxx 答：xxx），提取答案部分
        if "答：" in content:
            answer = content.split("答：", 1)[-1].strip()
            return f"{answer}\n\n还有什么想了解的吗？"
        
        # 如果是门店信息，提取关键信息
        if category == "门店" and ("地址" in message or "在哪" in message):
            # 提取地址信息
            if "水岸新都" in content:
                return """我们有两家门店：

📍 水岸新都店
地址：江阴市人民东路 1023 号佳兆业·水岸新都南区

📍 阳光国际店
地址：江阴市先锋路 98 号

电话：86281118
营业时间：08:15 - 20:30

需要导航吗？可以在小程序点击"导航"按钮哦！"""
        
        # 如果内容很长，截取前400字
        if len(content) > 400:
            content = content[:400] + "..."
        
        # 默认返回检索内容
        return f"{content}\n\n还有什么想了解的吗？"
    
    def _build_booking_response(self, docs: List[dict]) -> str:
        """
        构建预约咨询的回复
        """
        if not docs:
            return """您可以通过以下方式预约：

1. 小程序预约（推荐）
2. 电话预约：86281118

⚠️ 最多可预约未来 6 天内的时间"""
        
        # 提取最相关的预约信息
        content = docs[0]["content"]
        
        return content
    
    def _post_process_reply(self, reply: str, intent: str) -> str:
        """
        后处理 AI 回复：清理 Markdown + 添加 ACTION 标记
        """
        # 1. 清理 Markdown 格式符号
        # 去除加粗符号 **text**
        reply = re.sub(r'\*\*(.+?)\*\*', r'\1', reply)
        
        # 去除斜体符号 *text* 或 _text_（但要避免误伤列表项）
        reply = re.sub(r'(?<![\n\r])\*(.+?)\*', r'\1', reply)
        reply = re.sub(r'_(.+?)_', r'\1', reply)
        
        # 去除链接 [text](url)，保留 text
        reply = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', reply)
        
        # 去除代码块符号
        reply = re.sub(r'```[\s\S]*?```', '', reply)
        reply = re.sub(r'`(.+?)`', r'\1', reply)
        
        # 2. 根据意图添加 ACTION 标记
        if intent == intent_classifier.INTENT_CONSULT_BOOKING:
            # 如果还没有 ACTION 标记，添加跳转标记
            if "[ACTION:" not in reply:
                reply += "\n\n[ACTION:GOTO_BOOKING]"
        
        return reply