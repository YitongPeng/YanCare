"""
意图分类服务 - 基于关键词+规则
"""
import re
import jieba
from typing import Tuple, Optional


class IntentClassifier:
    """意图分类器"""
    
    # 意图类型定义
    INTENT_GREETING = "greeting"           # 问候
    INTENT_CONSULT_CARD = "consult_card"   # 咨询卡种
    INTENT_CONSULT_SERVICE = "consult_service"  # 咨询服务
    INTENT_CONSULT_BOOKING = "consult_booking"  # 咨询预约
    INTENT_CONSULT_STORE = "consult_store"      # 咨询门店
    INTENT_CONSULT_KNOWLEDGE = "consult_knowledge"  # 咨询养发知识
    INTENT_THANKS = "thanks"               # 感谢
    INTENT_GOODBYE = "goodbye"             # 再见
    INTENT_COMPLAINT = "complaint"         # 投诉反馈
    INTENT_OTHER = "other"                 # 其他
    
    def __init__(self):
        """初始化关键词库"""
        
        # 问候语关键词
        self.greeting_keywords = [
            "你好", "您好", "hi", "hello", "嗨", "哈喽", 
            "在吗", "在不在", "早上好", "下午好", "晚上好"
        ]
        
        # 卡种相关关键词
        self.card_keywords = [
            "卡", "办卡", "会员卡", "充值", "储值", 
            "价格", "多少钱", "费用", "收费", "优惠",
            "套餐", "划算", "哪种卡", "什么卡"
        ]
        
        # 服务项目关键词
        self.service_keywords = [
            "服务", "项目", "洗头", "泡头", "养发",
            "做什么", "有什么", "怎么做", "流程",
            "效果", "功效", "作用", "好处"
        ]
        
        # 预约相关关键词
        self.booking_keywords = [
            "预约", "约", "订", "安排", "时间",
            "怎么约", "如何约", "取消", "改约", 
            "爽约", "迟到", "提前", "当天"
        ]
        
        # 门店信息关键词
        self.store_keywords = [
            "门店", "店", "地址", "在哪", "位置",
            "电话", "联系", "营业时间", "几点", "开门",
            "水岸", "阳光", "怎么去", "路线", "交通"
        ]
        
        # 养发知识关键词
        self.knowledge_keywords = [
            "脱发", "掉发", "掉头发", "掉发多", "掉得多",
            "头发掉", "头发少", "头发稀", "发量少",
            "头发", "头皮", "油", "油腻", "出油",
            "干", "干燥", "痒", "屑", "头屑", 
            "白发", "少年白", "白头发",
            "生发", "防脱", "养护", "保养", "护理",
            "为什么", "原因", "怎么办", "如何", "多久",
            "经常掉", "大量掉", "严重"
        ]
        
        # 感谢关键词
        self.thanks_keywords = [
            "谢谢", "谢了", "多谢", "感谢", "太好了",
            "辛苦", "麻烦", "thanks", "thx"
        ]
        
        # 再见关键词
        self.goodbye_keywords = [
            "再见", "拜拜", "byebye", "bye", "88",
            "先走了", "走了", "下次聊"
        ]
        
        # 投诉反馈关键词
        self.complaint_keywords = [
            "投诉", "不满意", "差", "烂", "坑",
            "骗", "退款", "不好", "反馈", "建议"
        ]
    
    def classify(self, text: str) -> Tuple[str, float]:
        """
        分类用户意图
        
        Args:
            text: 用户输入文本
            
        Returns:
            (intent, confidence): 意图类型和置信度
        """
        text_lower = text.lower().strip()
        
        # 空消息
        if not text_lower:
            return self.INTENT_OTHER, 0.0
        
        # 使用jieba分词
        words = list(jieba.cut(text_lower))
        
        # 1. 问候语（优先级最高）
        if self._match_keywords(text_lower, words, self.greeting_keywords):
            return self.INTENT_GREETING, 0.95
        
        # 2. 感谢
        if self._match_keywords(text_lower, words, self.thanks_keywords):
            return self.INTENT_THANKS, 0.95
        
        # 3. 再见
        if self._match_keywords(text_lower, words, self.goodbye_keywords):
            return self.INTENT_GOODBYE, 0.95
        
        # 4. 投诉反馈
        if self._match_keywords(text_lower, words, self.complaint_keywords):
            return self.INTENT_COMPLAINT, 0.9
        
        # 5. 咨询类（需要检索知识库）
        
        # 5.1 卡种咨询
        card_score = self._calculate_match_score(text_lower, words, self.card_keywords)
        
        # 5.2 服务咨询
        service_score = self._calculate_match_score(text_lower, words, self.service_keywords)
        
        # 5.3 预约咨询
        booking_score = self._calculate_match_score(text_lower, words, self.booking_keywords)
        
        # 5.4 门店咨询
        store_score = self._calculate_match_score(text_lower, words, self.store_keywords)
        
        # 5.5 养发知识
        knowledge_score = self._calculate_match_score(text_lower, words, self.knowledge_keywords)
        
        # 找出最高分
        scores = {
            self.INTENT_CONSULT_CARD: card_score,
            self.INTENT_CONSULT_SERVICE: service_score,
            self.INTENT_CONSULT_BOOKING: booking_score,
            self.INTENT_CONSULT_STORE: store_score,
            self.INTENT_CONSULT_KNOWLEDGE: knowledge_score,
        }
        
        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]
        
        # 如果有明确匹配（分数>0.3），返回该意图
        if max_score > 0.3:
            return max_intent, min(max_score, 0.9)
        
        # 6. 其他（兜底）
        return self.INTENT_OTHER, 0.5
    
    def _match_keywords(self, text: str, words: list, keywords: list) -> bool:
        """检查是否匹配关键词"""
        for keyword in keywords:
            if keyword in text or keyword in words:
                return True
        return False
    
    def _calculate_match_score(self, text: str, words: list, keywords: list) -> float:
        """计算匹配分数"""
        match_count = 0
        for keyword in keywords:
            if keyword in text or keyword in words:
                match_count += 1
        
        if match_count == 0:
            return 0.0
        
        # 归一化分数（最高0.9）
        return min(match_count / len(keywords) * 5, 0.9)
    
    def is_need_rag(self, intent: str) -> bool:
        """判断该意图是否需要检索知识库"""
        # 咨询类意图需要检索
        consult_intents = [
            self.INTENT_CONSULT_CARD,
            self.INTENT_CONSULT_SERVICE,
            self.INTENT_CONSULT_BOOKING,
            self.INTENT_CONSULT_STORE,
            self.INTENT_CONSULT_KNOWLEDGE,
        ]
        return intent in consult_intents
    
    def get_intent_category(self, intent: str) -> Optional[str]:
        """
        获取意图对应的知识库类别
        用于针对性检索
        """
        intent_to_category = {
            self.INTENT_CONSULT_CARD: "卡种",
            self.INTENT_CONSULT_SERVICE: "服务",
            self.INTENT_CONSULT_BOOKING: "预约",
            self.INTENT_CONSULT_STORE: "门店",
            self.INTENT_CONSULT_KNOWLEDGE: "养发知识",
        }
        return intent_to_category.get(intent)


# 全局实例
intent_classifier = IntentClassifier()
