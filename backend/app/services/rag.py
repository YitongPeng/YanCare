"""
RAG 服务 - 检索增强生成
"""
import os
import re
from typing import List, Optional
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


class RAGService:
    """RAG 检索服务"""
    
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
                # 返回 None，后续只使用关键词匹配
                return None
        return self._embedding_fn
    
    @property
    def collection(self):
        """获取或创建知识库集合"""
        if self._collection is None:
            # 如果 embedding 函数加载失败，返回 None
            if self.embedding_fn is None:
                print("⚠️  向量检索不可用，仅使用关键词匹配")
                return None
            try:
                self._collection = self.client.get_or_create_collection(
                    name="yancare_knowledge_v2",  # 新版本，使用新模型
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
    
    def search(self, query: str, n_results: int = 3) -> List[dict]:
        """
        搜索相关知识（关键词优先 + 向量检索）
        
        Args:
            query: 用户问题
            n_results: 返回结果数量
            
        Returns:
            相关文档列表
        """
        documents = []
        
        # 1. 先尝试关键词匹配
        matched_id = self._keyword_match(query)
        if matched_id and self.collection is not None:
            try:
                result = self.collection.get(ids=[matched_id], include=["documents", "metadatas"])
                if result and result["documents"]:
                    documents.append({
                        "content": result["documents"][0],
                        "metadata": result["metadatas"][0] if result["metadatas"] else {},
                        "distance": 0,  # 关键词匹配，距离为0
                        "match_type": "keyword"
                    })
            except Exception as e:
                print(f"关键词匹配错误: {e}")
        
        # 2. 向量检索补充（仅当 collection 可用时）
        if self.collection is not None:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results + 2,  # 多检索几个
                    include=["documents", "metadatas", "distances"]
                )
                
                if results and results["documents"]:
                    for i, doc in enumerate(results["documents"][0]):
                        # 跳过已经通过关键词匹配的文档
                        if documents and doc == documents[0]["content"]:
                            continue
                        documents.append({
                            "content": doc,
                            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                            "distance": results["distances"][0][i] if results["distances"] else 0,
                            "match_type": "vector"
                        })
            except Exception as e:
                print(f"RAG 向量搜索错误: {e}")
        
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
            self.client.delete_collection("yancare_knowledge")
            self._collection = None
        except:
            pass
    
    def get_count(self) -> int:
        """获取知识库文档数量"""
        return self.collection.count()


# 全局实例
rag_service = RAGService()
