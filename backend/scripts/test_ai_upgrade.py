"""
AI 升级功能测试脚本
测试意图分类、混合检索、整体对话效果
"""
import os
import sys
from pathlib import Path
import asyncio

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.intent_classifier import intent_classifier
from app.services.rag_hybrid import hybrid_rag_service
from app.services.ai import AIService


def test_intent_classification():
    """测试意图分类"""
    print("=" * 60)
    print("🎯 测试意图分类")
    print("=" * 60)
    
    test_cases = [
        ("你好", "greeting"),
        ("您好呀", "greeting"),
        ("谢谢", "thanks"),
        ("再见", "goodbye"),
        ("办卡多少钱", "consult_card"),
        ("有什么卡", "consult_card"),
        ("什么服务", "consult_service"),
        ("泡头是什么", "consult_service"),
        ("怎么预约", "consult_booking"),
        ("可以取消吗", "consult_booking"),
        ("地址在哪", "consult_store"),
        ("门店电话", "consult_store"),
        ("脱发怎么办", "consult_knowledge"),
        ("养发多久做一次", "consult_knowledge"),
        ("不满意", "complaint"),
    ]
    
    correct = 0
    for query, expected_intent in test_cases:
        intent, confidence = intent_classifier.classify(query)
        is_correct = intent == expected_intent
        correct += is_correct
        
        status = "✅" if is_correct else "❌"
        print(f"{status} '{query}' -> {intent} (置信度: {confidence:.2f}) [期望: {expected_intent}]")
    
    accuracy = correct / len(test_cases) * 100
    print(f"\n准确率: {accuracy:.1f}% ({correct}/{len(test_cases)})\n")


def test_hybrid_search():
    """测试混合检索"""
    print("=" * 60)
    print("🔍 测试混合检索")
    print("=" * 60)
    
    # 检查知识库是否已加载
    doc_count = hybrid_rag_service.get_count()
    print(f"📚 知识库文档数: {doc_count}")
    
    if doc_count == 0:
        print("⚠️  知识库为空，请先运行 load_knowledge_base.py\n")
        return
    
    print()
    
    test_queries = [
        ("办卡多少钱", "卡种"),
        ("门店地址", "门店"),
        ("怎么预约", "预约"),
        ("脱发", "养发知识"),
        ("洗头", "服务"),
    ]
    
    for query, expected_category in test_queries:
        print(f"查询: '{query}' [期望类别: {expected_category}]")
        
        results = hybrid_rag_service.search(
            query, 
            n_results=3,
            use_reranking=True
        )
        
        if not results:
            print("  ❌ 没有检索到结果\n")
            continue
        
        # 检查第一个结果的类别是否匹配
        top_result = results[0]
        actual_category = top_result["metadata"].get("category", "unknown")
        is_correct = actual_category == expected_category
        
        status = "✅" if is_correct else "⚠️"
        print(f"  {status} Top1: [{actual_category}] {top_result['content'][:60]}...")
        print(f"     来源: {top_result.get('source', 'unknown')}, "
              f"RRF分数: {top_result.get('rrf_score', 0):.4f}, "
              f"最终分数: {top_result.get('final_score', 0):.4f}")
        print()


async def test_full_conversation():
    """测试完整对话流程"""
    print("=" * 60)
    print("💬 测试完整对话流程")
    print("=" * 60)
    
    ai_service = AIService()
    
    test_conversations = [
        "你好",
        "你们有什么卡？",
        "多少钱？",
        "门店地址在哪？",
        "谢谢",
    ]
    
    history = []
    
    for user_msg in test_conversations:
        print(f"\n👤 用户: {user_msg}")
        
        # 调用AI服务
        response = await ai_service.chat(user_msg, history=history)
        
        print(f"🤖 燕儿: {response}")
        
        # 更新历史
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": response})
        
        # 限制历史长度
        if len(history) > 10:
            history = history[-10:]
    
    print()


def main():
    """主函数"""
    print("\n")
    print("🚀 燕斛堂 AI 升级功能测试")
    print("=" * 60)
    print()
    
    # 测试1: 意图分类
    test_intent_classification()
    
    # 测试2: 混合检索
    test_hybrid_search()
    
    # 测试3: 完整对话
    print("按 Enter 继续测试完整对话流程...")
    input()
    asyncio.run(test_full_conversation())
    
    print("=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
