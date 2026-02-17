"""
混合检索服务 - 向量检索 + BM25 + Reranking
"""
import os
import jieba
from typing import List, Optional
from rank_bm25 import BM25Okapi
import chromadb
from chromadb.utils import embedding_functions

# 配置 Hugging Face 镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 知识库存储路径
CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "chroma_db")

# 使用中文优化的模型
EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"


class HybridRAGService:
    """混合检索 RAG 服务"""
    
    def __init__(self):
        self._client = None
        self._collection = None
        self._embedding_fn = None
        self._bm25 = None
        self._corpus = []  # 文档内容列表
        self._corpus_ids = []  # 文档ID列表
        self._corpus_metadata = []  # 文档元数据列表
    
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
                print("✅ 模型加载成功！")
            except Exception as e:
                print(f"⚠️  模型加载失败: {e}")
                print("⚠️  将使用降级方案（仅BM25检索）")
                return None
        return self._embedding_fn
    
    @property
    def collection(self):
        """获取或创建知识库集合"""
        if self._collection is None:
            if self.embedding_fn is None:
                print("⚠️  向量检索不可用")
                return None
            try:
                self._collection = self.client.get_or_create_collection(
                    name="yancare_kb_v2",
                    embedding_function=self.embedding_fn,
                    metadata={"description": "燕斛堂养发知识库 V2"}
                )
                print(f"✅ 知识库加载成功，文档数: {self._collection.count()}")
            except Exception as e:
                print(f"⚠️  知识库集合创建失败: {e}")
                return None
        return self._collection
    
    def _init_bm25(self):
        """初始化 BM25 索引"""
        if self._bm25 is not None:
            return
        
        print("正在初始化 BM25 索引...")
        
        try:
            # 从 ChromaDB 获取所有文档
            if self.collection is None:
                print("⚠️  无法初始化BM25：collection不可用")
                return
            
            all_docs = self.collection.get(include=["documents", "metadatas"])
            
            if not all_docs or not all_docs["documents"]:
                print("⚠️  知识库为空，请先加载文档")
                return
            
            self._corpus = all_docs["documents"]
            self._corpus_ids = all_docs["ids"]
            self._corpus_metadata = all_docs.get("metadatas", [{}] * len(self._corpus))
            
            # 分词
            tokenized_corpus = [list(jieba.cut(doc)) for doc in self._corpus]
            
            # 创建 BM25 索引
            self._bm25 = BM25Okapi(tokenized_corpus)
            
            print(f"✅ BM25 索引创建成功，文档数: {len(self._corpus)}")
            
        except Exception as e:
            print(f"⚠️  BM25 初始化失败: {e}")
            self._bm25 = None
    
    def search(
        self, 
        query: str, 
        n_results: int = 5,
        intent_category: Optional[str] = None,
        use_reranking: bool = True
    ) -> List[dict]:
        """
        混合检索
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            intent_category: 意图类别（用于过滤）
            use_reranking: 是否使用reranking
            
        Returns:
            文档列表
        """
        # 确保 BM25 已初始化
        if self._bm25 is None:
            self._init_bm25()
        
        # 1. 向量检索
        vector_results = self._vector_search(query, n_results * 2, intent_category)
        
        # 2. BM25 检索
        bm25_results = self._bm25_search(query, n_results * 2, intent_category)
        
        # 3. RRF 融合
        fused_results = self._reciprocal_rank_fusion(
            [vector_results, bm25_results],
            k=60
        )
        
        # 4. Reranking（可选）
        if use_reranking and len(fused_results) > 0:
            fused_results = self._rerank_by_relevance(fused_results, query)
        
        # 5. 返回 Top N
        return fused_results[:n_results]
    
    def _vector_search(
        self, 
        query: str, 
        n_results: int,
        category_filter: Optional[str] = None
    ) -> List[dict]:
        """向量检索"""
        if self.collection is None:
            return []
        
        try:
            # 构建过滤条件
            where = None
            if category_filter:
                where = {"category": category_filter}
            
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            if not results or not results["documents"]:
                return []
            
            documents = []
            for i, doc in enumerate(results["documents"][0]):
                documents.append({
                    "id": results["ids"][0][i] if "ids" in results else f"vec_{i}",
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 1.0,
                    "source": "vector",
                    "score": 1 / (1 + results["distances"][0][i]) if results["distances"] else 0.5
                })
            
            return documents
            
        except Exception as e:
            print(f"⚠️  向量检索错误: {e}")
            return []
    
    def _bm25_search(
        self, 
        query: str, 
        n_results: int,
        category_filter: Optional[str] = None
    ) -> List[dict]:
        """BM25 检索"""
        if self._bm25 is None:
            return []
        
        try:
            # 分词
            tokenized_query = list(jieba.cut(query))
            
            # BM25 打分
            scores = self._bm25.get_scores(tokenized_query)
            
            # 获取 top N
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            
            documents = []
            for idx in top_indices[:n_results]:
                # 类别过滤
                if category_filter:
                    doc_category = self._corpus_metadata[idx].get("category", "")
                    if doc_category != category_filter:
                        continue
                
                documents.append({
                    "id": self._corpus_ids[idx],
                    "content": self._corpus[idx],
                    "metadata": self._corpus_metadata[idx],
                    "distance": 1 - scores[idx] / max(scores) if max(scores) > 0 else 1.0,
                    "source": "bm25",
                    "score": scores[idx]
                })
            
            return documents
            
        except Exception as e:
            print(f"⚠️  BM25 检索错误: {e}")
            return []
    
    def _reciprocal_rank_fusion(
        self, 
        rankings: List[List[dict]], 
        k: int = 60
    ) -> List[dict]:
        """
        RRF（Reciprocal Rank Fusion）融合多个检索结果
        
        Args:
            rankings: 多个检索结果列表
            k: RRF 参数（默认60）
            
        Returns:
            融合后的结果
        """
        # 文档ID -> 融合分数
        doc_scores = {}
        # 文档ID -> 文档对象
        doc_objects = {}
        
        for ranking in rankings:
            for rank, doc in enumerate(ranking, start=1):
                doc_id = doc["id"]
                
                # RRF 分数: 1 / (k + rank)
                rrf_score = 1 / (k + rank)
                
                if doc_id in doc_scores:
                    doc_scores[doc_id] += rrf_score
                else:
                    doc_scores[doc_id] = rrf_score
                    doc_objects[doc_id] = doc
        
        # 按分数排序
        sorted_doc_ids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)
        
        # 构建结果
        fused_results = []
        for doc_id in sorted_doc_ids:
            doc = doc_objects[doc_id].copy()
            doc["rrf_score"] = doc_scores[doc_id]
            fused_results.append(doc)
        
        return fused_results
    
    def _rerank_by_relevance(self, documents: List[dict], query: str) -> List[dict]:
        """
        基于关键词重叠度重排序
        
        Args:
            documents: 文档列表
            query: 查询文本
            
        Returns:
            重排序后的文档列表
        """
        # 查询分词
        query_tokens = set(jieba.cut(query.lower()))
        
        for doc in documents:
            content = doc["content"].lower()
            content_tokens = set(jieba.cut(content))
            
            # 计算 Jaccard 相似度
            intersection = query_tokens & content_tokens
            union = query_tokens | content_tokens
            
            jaccard = len(intersection) / len(union) if len(union) > 0 else 0
            
            # 综合分数：RRF分数 + Jaccard相似度
            original_score = doc.get("rrf_score", 0)
            doc["final_score"] = original_score * 0.7 + jaccard * 0.3
        
        # 按最终分数排序
        documents.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        return documents
    
    def get_count(self) -> int:
        """获取知识库文档数量"""
        if self.collection is None:
            return 0
        try:
            return self.collection.count()
        except:
            return 0


# 全局实例
hybrid_rag_service = HybridRAGService()
