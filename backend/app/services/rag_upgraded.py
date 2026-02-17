"""
RAG 服务 - 升级版（带重排序和混合检索）
"""
import os
import re
from typing import List, Optional
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions

# 配置 Hugging Face 镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 知识库存储路径
CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "chroma_db")

# 使用中文优化的模型
EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"


# 关键词映射：当用户问到某些关键词时，优先返回特定文档
KEYWORD_MAP = {
    ("卡", "卡种", "有什么卡", "哪些卡"): "card_overview",
    ("养发频率", "多久做一次", "养发多久", "几天做一次"): "faq_care_freq",
    ("什么服务", "有什么服务", "做什么的", "项目"): "service_overview",
    ("在哪", "地址", "门店", "哪里"): "store_info",
    ("价格", "多少钱", "收费"): "card_overview",
}

# 同义词映射（查询扩展）
SYNONYMS = {
    "掉发": ["脱发", "掉头发", "头发掉", "脱落"],
    "养发": ["护发", "头发护理", "头发养护", "养护头发"],
    "价格": ["多少钱", "费用", "收费", "花费"],
    "洗头": ["洗发", "洗头发"],
    "泡头": ["头疗", "头部护理"],
}


class RAGServiceUpgraded:
    """RAG 检索服务 - 升级版"""
    
    def __init__(self):
        self._client = None
        self._collection = None
        self._embedding_fn = None
        self._docs_cache = {}  # 缓存文档内容
    
    @property
    def client(self):
        """懒加载 ChromaDB 客户端"""
        if self._client is None:
            self._client = chromadb.PersistentClient(path=CHROMA_PATH)
        return self._client
    
    @property
    def embedding_fn(self):
        """懒加载 Embedding 函数"""
        if self._embedding_fn is None:
            try:
                print(f"正在加载 embedding 模型: {EMBEDDING_MODEL}...")
                self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=EMBEDDING_MODEL
                )
                print("模型加载成功！")
            except Exception as e:
                print(f"⚠️  模型加载失败: {e}")
                print("⚠️  将使用降级方案（仅关键词匹配）")
                return None
        return self._embedding_fn
    
    @property
    def collection(self):
        """获取或创建知识库集合"""
        if self._collection is None:
            if self.embedding_fn is None:
                print("⚠️  向量检索不可用，仅使用关键词匹配")
                return None
            try:
                self._collection = self.client.get_or_create_collection(
                    name="yancare_knowledge_v2",
                    embedding_function=self.embedding_fn,
                    metadata={"description": "燕斛堂养发知识库"}
                )
            except Exception as e:
                print(f"⚠️  知识库集合创建失败: {e}")
                return None
        return self._collection
    
    def _keyword_match(self, query: str) -> Optional[str]:
        """关键词匹配，返回文档ID"""
        query_lower = query.lower()
        for keywords, doc_id in KEYWORD_MAP.items():
            for kw in keywords:
                if kw in query_lower:
                    return doc_id
        return None
    
    def _expand_query(self, query: str) -> List[str]:
        """
        查询扩展：添加同义词
        
        示例：
        输入："掉发怎么办"
        输出：["掉发怎么办", "脱发怎么办", "掉头发怎么办", "头发掉怎么办"]
        """
        expanded_queries = [query]
        
        for word, synonyms in SYNONYMS.items():
            if word in query:
                for syn in synonyms:
                    expanded_queries.append(query.replace(word, syn))
        
        return expanded_queries
    
    def _rerank_by_relevance(self, documents: List[dict], query: str) -> List[dict]:
        """
        重排序：基于多个因素重新排序
        
        考虑因素：
        1. 原始相似度分数
        2. 匹配类型（关键词 > 向量）
        3. 文档类型（FAQ > 普通知识）
        4. 文档新鲜度（可选）
        """
        for doc in documents:
            score = 0
            
            # 1. 原始相似度（距离越小越好，转换为分数：1 - distance）
            if 'distance' in doc:
                score += (1 - doc['distance']) * 0.5
            
            # 2. 匹配类型权重
            if doc.get('match_type') == 'keyword':
                score += 0.3  # 关键词匹配额外加分
            
            # 3. 文档类型权重
            metadata = doc.get('metadata', {})
            category = metadata.get('category', '')
            if category in ['FAQ', '常见问题']:
                score += 0.2  # FAQ 文档额外加分
            
            # 4. 查询关键词覆盖度
            content = doc['content'].lower()
            query_words = query.lower().split()
            matched_words = sum(1 for word in query_words if word in content)
            coverage = matched_words / len(query_words) if query_words else 0
            score += coverage * 0.1
            
            doc['rerank_score'] = score
        
        # 按重排序分数排序
        return sorted(documents, key=lambda x: x.get('rerank_score', 0), reverse=True)
    
    def _reciprocal_rank_fusion(self, rankings: List[List[dict]], k: int = 60) -> List[dict]:
        """
        RRF 算法：融合多个排名
        
        公式：RRF(D) = Σ 1/(k + r_i(D))
        - D: 文档
        - r_i(D): 文档 D 在第 i 个排名中的位置
        - k: 常数（通常是 60）
        """
        # 收集所有文档
        all_docs = {}
        for ranking in rankings:
            for rank, doc in enumerate(ranking, start=1):
                doc_id = doc.get('id', doc.get('content', '')[:50])
                
                if doc_id not in all_docs:
                    all_docs[doc_id] = {
                        'doc': doc,
                        'rrf_score': 0
                    }
                
                # RRF 公式
                all_docs[doc_id]['rrf_score'] += 1 / (k + rank)
        
        # 排序并返回
        sorted_docs = sorted(
            all_docs.values(),
            key=lambda x: x['rrf_score'],
            reverse=True
        )
        
        return [item['doc'] for item in sorted_docs]
    
    def search(self, query: str, n_results: int = 3, use_reranking: bool = True) -> List[dict]:
        """
        搜索相关知识（升级版）
        
        工作流程：
        1. 查询扩展（同义词）
        2. 关键词匹配
        3. 向量检索
        4. 重排序（可选）
        
        Args:
            query: 用户问题
            n_results: 返回结果数量
            use_reranking: 是否使用重排序
            
        Returns:
            相关文档列表
        """
        documents = []
        
        # 1. 查询扩展
        expanded_queries = self._expand_query(query)
        print(f"查询扩展: {query} → {expanded_queries}")
        
        # 2. 关键词匹配
        matched_id = self._keyword_match(query)
        if matched_id and self.collection is not None:
            try:
                result = self.collection.get(ids=[matched_id], include=["documents", "metadatas"])
                if result and result["documents"]:
                    documents.append({
                        "id": matched_id,
                        "content": result["documents"][0],
                        "metadata": result["metadatas"][0] if result["metadatas"] else {},
                        "distance": 0,  # 关键词匹配，距离为0
                        "match_type": "keyword"
                    })
                    print(f"关键词匹配成功: {matched_id}")
            except Exception as e:
                print(f"关键词匹配错误: {e}")
        
        # 3. 向量检索（使用扩展查询）
        if self.collection is not None:
            all_vector_results = []
            
            for expanded_query in expanded_queries[:3]:  # 最多使用前 3 个扩展查询
                try:
                    results = self.collection.query(
                        query_texts=[expanded_query],
                        n_results=n_results * 2,  # 多检索一些候选
                        include=["documents", "metadatas", "distances"]
                    )
                    
                    if results and results["documents"]:
                        for i, doc in enumerate(results["documents"][0]):
                            # 跳过已经通过关键词匹配的文档
                            if documents and doc == documents[0]["content"]:
                                continue
                            
                            # 避免重复
                            if any(d['content'] == doc for d in documents):
                                continue
                            
                            documents.append({
                                "content": doc,
                                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                                "distance": results["distances"][0][i] if results["distances"] else 0,
                                "match_type": "vector",
                                "query": expanded_query  # 记录是哪个查询匹配的
                            })
                
                except Exception as e:
                    print(f"向量搜索错误 (查询: {expanded_query}): {e}")
        
        # 4. 重排序
        if use_reranking and documents:
            print(f"重排序前: {len(documents)} 个文档")
            documents = self._rerank_by_relevance(documents, query)
            print(f"重排序完成")
        
        # 返回 top-k 结果
        return documents[:n_results]
    
    def add_documents(self, documents: List[dict]):
        """
        添加文档到知识库
        
        Args:
            documents: 文档列表，每个文档包含 id, content, metadata
        """
        if not documents:
            return
        
        ids = [doc["id"] for doc in documents]
        contents = [doc["content"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        
        self.collection.add(
            ids=ids,
            documents=contents,
            metadatas=metadatas
        )
    
    def clear(self):
        """清空知识库"""
        try:
            self.client.delete_collection("yancare_knowledge_v2")
            self._collection = None
        except:
            pass
    
    def get_count(self) -> int:
        """获取知识库文档数量"""
        if self.collection is None:
            return 0
        return self.collection.count()


# 全局实例
rag_service_upgraded = RAGServiceUpgraded()


# ==================== 使用示例 ====================

if __name__ == "__main__":
    """测试升级后的 RAG 服务"""
    
    # 测试查询
    test_queries = [
        "养发多久做一次好？",
        "我经常掉发怎么办？",
        "你们有什么卡？",
        "门店在哪里？",
    ]
    
    print("=" * 60)
    print("测试升级版 RAG 服务")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n查询: {query}")
        print("-" * 60)
        
        results = rag_service_upgraded.search(query, n_results=3)
        
        if not results:
            print("没有找到相关文档")
            continue
        
        for i, doc in enumerate(results, 1):
            print(f"\n结果 {i}:")
            print(f"  匹配方式: {doc.get('match_type', 'unknown')}")
            if 'query' in doc:
                print(f"  匹配查询: {doc['query']}")
            print(f"  相似度分数: {doc.get('distance', 0):.3f}")
            if 'rerank_score' in doc:
                print(f"  重排序分数: {doc['rerank_score']:.3f}")
            print(f"  内容预览: {doc['content'][:100]}...")
            print(f"  元数据: {doc.get('metadata', {})}")
