"""
知识库文档加载脚本
将 markdown 文档切块、生成 embedding、存入 ChromaDB
"""
import os
import sys
import re
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.rag_hybrid import hybrid_rag_service


# 知识库文档目录
KNOWLEDGE_BASE_DIR = os.path.join(
    os.path.dirname(project_root),
    "知识库文档"
)


class DocumentLoader:
    """文档加载器"""
    
    def __init__(self, kb_dir: str):
        self.kb_dir = kb_dir
        self.documents = []
    
    def load_all_documents(self):
        """加载所有markdown文档"""
        print(f"📂 正在从目录加载文档: {self.kb_dir}")
        
        if not os.path.exists(self.kb_dir):
            print(f"❌ 目录不存在: {self.kb_dir}")
            return []
        
        # 文档文件映射
        doc_files = {
            "1-常见问题FAQ.md": "FAQ",
            "2-卡种介绍.md": "卡种",
            "3-服务项目介绍.md": "服务",
            "4-产品介绍.md": "产品",
            "5-门店信息.md": "门店",
            "6-养发知识科普.md": "养发知识",
            "7-预约和使用指南.md": "预约",
        }
        
        for filename, category in doc_files.items():
            filepath = os.path.join(self.kb_dir, filename)
            if os.path.exists(filepath):
                print(f"  📄 加载: {filename}")
                self._load_single_document(filepath, category)
            else:
                print(f"  ⚠️  文件不存在: {filename}")
        
        print(f"✅ 共加载 {len(self.documents)} 个文档块\n")
        return self.documents
    
    def _load_single_document(self, filepath: str, category: str):
        """加载单个文档并切块"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 获取文档名（不含扩展名）
        doc_name = os.path.splitext(os.path.basename(filepath))[0]
        
        # 根据文档类型选择切块策略
        if category == "FAQ":
            chunks = self._chunk_faq(content, doc_name, category)
        else:
            chunks = self._chunk_by_section(content, doc_name, category)
        
        self.documents.extend(chunks)
    
    def _chunk_faq(self, content: str, doc_name: str, category: str) -> list:
        """
        FAQ 文档按问答对切块
        每个 Q&A 是一个独立的 chunk
        """
        chunks = []
        
        # 按 ### Q 分割（修复：只需要一个换行符）
        qa_pattern = r'###\s*Q\d+[：:]\s*(.+?)\n\*\*答[：:]\*\*\s*(.+?)(?=\n###|$)'
        matches = re.findall(qa_pattern, content, re.DOTALL)
        
        for i, (question, answer) in enumerate(matches):
            question = question.strip()
            answer = answer.strip()
            
            # 清理 Markdown 格式符号
            question = self._clean_markdown(question)
            answer = self._clean_markdown(answer)
            
            # 组合问答
            chunk_content = f"问：{question}\n答：{answer}"
            
            chunks.append({
                "id": f"{doc_name}_q{i+1}",
                "content": chunk_content,
                "metadata": {
                    "source": doc_name,
                    "category": category,
                    "type": "faq",
                    "question": question,
                    "chunk_index": i
                }
            })
        
        print(f"    ✂️  切块: {len(chunks)} 个问答对")
        return chunks
    
    def _chunk_by_section(self, content: str, doc_name: str, category: str) -> list:
        """
        普通文档按章节切块
        每个 ## 或 ### 是一个 chunk
        """
        chunks = []
        
        # 按标题分割（## 或 ###）
        sections = re.split(r'\n(?=##\s)', content)
        
        for i, section in enumerate(sections):
            section = section.strip()
            
            # 跳过空章节和太短的内容
            if not section or len(section) < 50:
                continue
            
            # 提取标题
            title_match = re.match(r'##\s*(.+)', section)
            title = title_match.group(1).strip() if title_match else "未命名章节"
            
            # 清理 Markdown 格式
            section_clean = self._clean_markdown(section)
            
            # 如果章节过长（>800字），进一步切分
            if len(section_clean) > 800:
                sub_chunks = self._split_long_section(section_clean, doc_name, category, title, i)
                chunks.extend(sub_chunks)
            else:
                chunks.append({
                    "id": f"{doc_name}_sec{i}",
                    "content": section_clean,
                    "metadata": {
                        "source": doc_name,
                        "category": category,
                        "type": "section",
                        "title": title,
                        "chunk_index": i
                    }
                })
        
        print(f"    ✂️  切块: {len(chunks)} 个章节")
        return chunks
    
    def _clean_markdown(self, text: str) -> str:
        """
        清理 Markdown 格式符号，保留纯文本
        """
        # 去除加粗符号 **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        
        # 去除斜体符号 *text* 或 _text_
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        
        # 去除链接 [text](url)，保留 text
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        
        # 去除标题符号 ## 、### 等
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # 去除列表符号 - 或 * 或 数字.
        text = re.sub(r'^[\-\*]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # 去除代码块符号 ``` 
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        
        return text
    
    def _split_long_section(
        self, 
        section: str, 
        doc_name: str, 
        category: str, 
        title: str, 
        section_idx: int
    ) -> list:
        """将过长的章节进一步切分"""
        chunks = []
        
        # 按段落分割
        paragraphs = section.split('\n\n')
        
        current_chunk = ""
        chunk_count = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 如果加上当前段落不超过600字，继续累积
            if len(current_chunk) + len(para) < 600:
                current_chunk += para + "\n\n"
            else:
                # 保存当前chunk
                if current_chunk:
                    chunks.append({
                        "id": f"{doc_name}_sec{section_idx}_sub{chunk_count}",
                        "content": current_chunk.strip(),
                        "metadata": {
                            "source": doc_name,
                            "category": category,
                            "type": "section",
                            "title": title,
                            "chunk_index": section_idx,
                            "sub_index": chunk_count
                        }
                    })
                    chunk_count += 1
                
                # 开始新chunk
                current_chunk = para + "\n\n"
        
        # 保存最后一个chunk
        if current_chunk:
            chunks.append({
                "id": f"{doc_name}_sec{section_idx}_sub{chunk_count}",
                "content": current_chunk.strip(),
                "metadata": {
                    "source": doc_name,
                    "category": category,
                    "type": "section",
                    "title": title,
                    "chunk_index": section_idx,
                    "sub_index": chunk_count
                }
            })
        
        return chunks


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 燕斛堂知识库加载工具")
    print("=" * 60)
    print()
    
    # 1. 加载文档
    loader = DocumentLoader(KNOWLEDGE_BASE_DIR)
    documents = loader.load_all_documents()
    
    if not documents:
        print("❌ 没有文档可加载，退出")
        return
    
    # 2. 清空旧数据（可选）
    print("🗑️  准备清空旧知识库...")
    try:
        collection = hybrid_rag_service.collection
        if collection and collection.count() > 0:
            # 获取所有ID并删除
            all_docs = collection.get()
            if all_docs and all_docs["ids"]:
                collection.delete(ids=all_docs["ids"])
                print(f"✅ 已清空 {len(all_docs['ids'])} 个旧文档\n")
    except Exception as e:
        print(f"⚠️  清空旧数据失败: {e}\n")
    
    # 3. 写入新数据
    print("💾 正在写入知识库...")
    try:
        collection = hybrid_rag_service.collection
        if collection is None:
            print("❌ 无法获取 collection，请检查 embedding 模型")
            return
        
        # 批量写入
        ids = [doc["id"] for doc in documents]
        contents = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        
        collection.add(
            ids=ids,
            documents=contents,
            metadatas=metadatas
        )
        
        print(f"✅ 成功写入 {len(documents)} 个文档块\n")
        
    except Exception as e:
        print(f"❌ 写入失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. 验证
    print("🔍 验证知识库...")
    doc_count = hybrid_rag_service.get_count()
    print(f"✅ 当前知识库文档数: {doc_count}\n")
    
    # 5. 测试检索
    print("🧪 测试检索功能...")
    test_queries = [
        "你们有什么卡？",
        "门店地址在哪？",
        "怎么预约？"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        results = hybrid_rag_service.search(query, n_results=2)
        for i, doc in enumerate(results, 1):
            print(f"  {i}. [{doc['metadata'].get('category', 'unknown')}] {doc['content'][:50]}...")
    
    print("\n" + "=" * 60)
    print("🎉 知识库加载完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
