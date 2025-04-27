import requests
import json
from typing import Dict, Tuple, List
import logging
import re
import numpy as np
from ai_audit_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, BUSINESS_SPECIFIC_RULES
from sentence_transformers import SentenceTransformer
import faiss


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_audit.log'),
        logging.StreamHandler()
    ]
)

class AIAuditor:
    def __init__(self):
        """
        初始化AI审核器，API密钥直接在类中定义
        """
        self.api_endpoint = "https://api.deepseek.com/chat/completions"
        self.api_key = "sk-fdb5269b9e0e43aca3cf7dea21d63322"  # 直接使用固定的API密钥
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 使用系统提示词
        self.system_prompt = SYSTEM_PROMPT
        # 添加token计数器
        self.total_tokens_used = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        
        # 向量化和缓存相关设置
        self.vector_enabled = True
        if self.vector_enabled:
            # 初始化文本向量化模型
            try:
                # 模型参数设置
                self.model_name = 'BAAI/bge-small-zh-v1.5'  # 更改为你要使用的模型
                self.normalize_vectors = True  # BAAI模型推荐归一化向量
                
                logging.info(f"正在加载模型: {self.model_name}")
                self.embedder = SentenceTransformer(self.model_name)
                
                # 通过测试获取实际向量维度
                test_text = "测试文本"
                test_vector = self.embedder.encode([test_text], show_progress_bar=False)[0]
                self.vector_dim = test_vector.shape[0]
                logging.info(f"成功加载模型: {self.model_name}, 向量维度: {self.vector_dim}")
                
                # 初始化向量索引
                self.index = faiss.IndexFlatL2(self.vector_dim)
                
                # 初始化缓存
                self.sms_cache = []  # 存储短信文本
                self.result_cache = []  # 存储对应审核结果
                self.similarity_threshold = 0.45  # 相似度阈值
                logging.info("向量化和缓存功能已初始化")
            except Exception as e:
                import traceback
                self.vector_enabled = False
                logging.error(f"向量化功能初始化失败: {str(e)}\n{traceback.format_exc()}")
        else:
            logging.info("向量化功能未启用，将使用常规审核方法")

    def _process_api_response(self, response, method_name=""):
        """
        处理API响应的通用方法，提取并处理结果
        
        Args:
            response: API响应对象
            method_name: 调用方法名称，用于日志区分
            
        Returns:
            Tuple[bool, Dict]: (是否通过审核, 审核结果详情)
        """
        try:
            if response.status_code == 200:
                result = response.json()
                ai_response = result["choices"][0]["message"]["content"]
                
                # 记录token使用情况
                usage = result.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
                
                # 更新总计数器
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                self.total_tokens_used += total_tokens
                
                # 记录本次调用的token使用情况
                logging.info(f"{method_name} Token使用: 输入={input_tokens}, 输出={output_tokens}, 总计={total_tokens}")
                
                # 去除可能存在的代码块标记
                clean_response = ai_response
                
                # 去除开头的代码块标记 (```json)
                code_block_start = re.search(r'^```(?:json)?', clean_response)
                if code_block_start:
                    clean_response = clean_response[code_block_start.end():].strip()
                
                # 去除结尾的代码块标记 (```)
                code_block_end = re.search(r'```$', clean_response)
                if code_block_end:
                    clean_response = clean_response[:code_block_end.start()].strip()
                
                # 解析清理后的JSON
                audit_result = json.loads(clean_response)
                
                # 将token使用情况添加到审核结果中
                audit_result["token_usage"] = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens
                }
                
                return audit_result["should_pass"], audit_result
            else:
                error_msg = f"API调用失败: {response.status_code}"
                if hasattr(response, 'text'):
                    error_msg += f", {response.text}"
                logging.error(f"{method_name} {error_msg}")
                return False, {"error": error_msg}
                
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析错误: {str(e)}, 响应内容: {response.text if hasattr(response, 'text') else 'Unknown'}"
            logging.error(f"{method_name} {error_msg}")
            return False, {"error": error_msg}
        except Exception as e:
            logging.error(f"{method_name} 处理API响应出错: {str(e)}")
            return False, {"error": str(e)}


    def audit_sms(self, signature: str, content: str, business_type: str) -> Tuple[bool, Dict]:
        """
        对单条短信进行AI审核
        
        Args:
            signature: 短信签名
            content: 短信内容
            business_type: 业务类型
            
        Returns:
            Tuple[bool, Dict]: (是否通过审核, 审核结果详情)
        """
        try:
            import time
            api_start_time = time.time()
            
            # 获取业务特定规则
            business_specific_rules = BUSINESS_SPECIFIC_RULES.get(
                business_type, 
                "此业务类型没有特定规则，请使用通用审核标准进行评估。"
            )
            
            # 构建用户提示词，中包含了短信
            user_prompt = USER_PROMPT_TEMPLATE.format(
                signature=signature,
                content=content,
                business_type=business_type,
                business_specific_rules=business_specific_rules
            )

            # 构建请求数据，传入系统提示词和用户提示词
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1  # 降低随机性，使输出更确定
            }

            # 发送请求
            response = requests.post(
                self.api_endpoint,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            # 计算API调用耗时
            api_time = time.time() - api_start_time
            logging.info(f"API调用耗时: {api_time:.2f}秒")
            
            # 处理响应
            passed, result = self._process_api_response(response, "标准审核")
            
            # 将API调用时间添加到结果中
            if isinstance(result, dict):
                result["api_time"] = api_time
                
            return passed, result

        except Exception as e:
            logging.error(f"AI审核过程出错: {str(e)}")
            return False, {"error": str(e)}

    def batch_audit(self, sms_list: List[Dict]) -> List[Dict]:
        """
        批量审核短信
        
        Args:
            sms_list: 短信列表，每个元素包含 signature, content, business_type
            
        Returns:
            List[Dict]: 审核结果列表，每个元素包含 sms, passed, details
        """
        results = []
        total = len(sms_list)
        
        # 重置token计数器
        self.total_tokens_used = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        
        # 记录开始时间和缓存命中计数
        import time
        start_time = time.time()
        cache_hits = 0
        
        logging.info(f"开始批量审核 {total} 条短信")   
        
        for i, sms in enumerate(sms_list):
            try:
                # 记录进度
                if i % 10 == 0 or i == total - 1:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / (i + 1) if i > 0 else 0
                    eta = avg_time * (total - i - 1) if i > 0 else 0
                    hit_rate = (cache_hits / (i + 1)) * 100 if i >= 0 else 0
                    logging.info(f"进度: {i+1}/{total} [{hit_rate:.1f}% 缓存命中] [平均 {avg_time:.2f}秒/条] [预计剩余 {eta:.0f}秒]")
                
                # 优先使用缓存版本
                if self.vector_enabled:
                    passed, details = self.audit_sms_with_cache(
                        sms["signature"], 
                        sms["content"], 
                        sms["business_type"]
                    )
                    # 检查是否命中缓存
                    if isinstance(details, dict) and details.get("cached", False):
                        cache_hits += 1
                else:
                    # 否则使用常规方法
                    passed, details = self.audit_sms(
                        sms["signature"], 
                        sms["content"], 
                        sms["business_type"]
                    )
                
                # 添加结果
                results.append({
                    "sms": sms,
                    "passed": passed,
                    "details": details
                })
                
            except Exception as e:
                logging.error(f"审核第 {i+1} 条短信时出错: {str(e)}")
                # 添加错误结果，确保结果列表的长度与输入一致
                results.append({
                    "sms": sms,
                    "passed": False,  # 出错时默认不通过
                    "details": {"error": str(e)}
                })
        
        # 计算缓存命中率
        if self.vector_enabled:
            hit_rate = (cache_hits / total) * 100 if total > 0 else 0
            logging.info(f"缓存命中: {cache_hits}/{total} ({hit_rate:.1f}%)")
        
        # 记录总token使用情况
        total_time = time.time() - start_time
        logging.info(f"批量审核完成，共处理 {len(results)} 条短信，总耗时: {total_time:.2f}秒，平均每条: {total_time/len(results):.2f}秒")
        logging.info(f"总Token消耗: 输入={self.total_input_tokens}, 输出={self.total_output_tokens}, 总计={self.total_tokens_used}")
        logging.info(f"平均每条短信Token消耗: {self.total_tokens_used / len(results) if results else 0:.2f}")
        
        return results
    
    def audit_sms_with_cache(self, signature: str, content: str, business_type: str) -> Tuple[bool, Dict]:
        """
        使用缓存机制对短信进行AI审核
        
        Args:
            signature: 短信签名
            content: 短信内容
            business_type: 业务类型
            
        Returns:
            Tuple[bool, Dict]: (是否通过审核, 审核结果详情)
        """
        # 构建完整的短信文本用于相似度比较
        sms_text = f"{signature} {content} {business_type}"
        
        # 如果向量化功能启用，尝试从缓存获取结果
        if self.vector_enabled:
            try:
                cached_result, similarity = self.find_similar_sms(sms_text)
                
                if cached_result:
                    logging.info(f"从缓存获取结果，相似度: {similarity:.4f}")
                    
                    # 添加缓存标记到结果中
                    result_copy = cached_result.copy()
                    if "details" in result_copy and isinstance(result_copy["details"], dict):
                        if "cached" not in result_copy["details"]:
                            result_copy["details"]["cached"] = True
                            result_copy["details"]["similarity_score"] = float(similarity)
                    
                    return result_copy["passed"], result_copy["details"]
            except Exception as e:
                logging.warning(f"从缓存获取结果失败: {str(e)}，将直接调用API")
        
        # 没有缓存命中或缓存检索出错，调用API审核
        passed, result = self.audit_sms(signature, content, business_type)
        
        # 如果向量化功能启用，缓存结果
        if self.vector_enabled:
            try:
                self.cache_result(sms_text, {
                    "passed": passed,
                    "details": result
                })
            except Exception as e:
                logging.warning(f"缓存结果失败: {str(e)}")
        
        return passed, result
    

    def get_embedding(self, text):
        """
        将文本转换为向量
        
        Args:
            text: 要向量化的文本
            
        Returns:
            numpy.ndarray: 文本向量
        """
        if not self.vector_enabled:
            return None
            
        try:
            # 获取向量
            vector = self.embedder.encode([text], show_progress_bar=False)[0]
            
            # 检查向量的形状和类型
            logging.debug(f"获取到向量: shape={vector.shape}, dtype={vector.dtype}")
            
            # BAAI模型可能需要的额外处理（如归一化）
            # 某些BAAI模型推荐对向量进行归一化处理，提高结果质量
            vector_norm = np.linalg.norm(vector)
            if vector_norm > 0:
                vector = vector / vector_norm
                logging.debug("向量已归一化")
            
            return vector
        except Exception as e:
            import traceback
            logging.error(f"文本向量化失败: {str(e)}\n{traceback.format_exc()}")
            return None
    
    def batch_get_embeddings(self, texts):
        """
        批量获取文本向量
        
        Args:
            texts: 要向量化的文本列表
            
        Returns:
            numpy.ndarray: 文本向量数组，失败的向量为None
        """
        if not self.vector_enabled:
            return None
            
        try:
            # 批量获取向量
            embeddings = self.embedder.encode(texts, show_progress_bar=False)
            
            # 检查向量形状
            logging.debug(f"批量获取向量: count={len(texts)}, shape={embeddings.shape}, dtype={embeddings.dtype}")
            
            # 如果启用了归一化，对所有向量进行归一化处理
            if hasattr(self, 'normalize_vectors') and self.normalize_vectors:
                # 计算每个向量的模长
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                # 只归一化非零向量
                non_zero_norm_indices = norms.flatten() > 0
                embeddings[non_zero_norm_indices] = embeddings[non_zero_norm_indices] / norms[non_zero_norm_indices]
                logging.debug("批量向量已归一化")
            
            return embeddings
        except Exception as e:
            import traceback
            logging.error(f"批量文本向量化失败: {str(e)}\n{traceback.format_exc()}")
            # 尝试逐个处理
            results = []
            for text in texts:
                try:
                    vec = self.get_embedding(text)  # 使用单个处理函数，确保一致性
                    if vec is not None:
                        results.append(vec)
                    else:
                        logging.warning(f"单条文本向量化失败: {text[:30]}...")
                except Exception as ex:
                    logging.warning(f"单条文本向量化出错: {str(ex)}")
                    results.append(None)
                
            if results:
                return np.array([r for r in results if r is not None])
            return np.array([])
            
    def find_similar_sms(self, sms_text):
        """
        在缓存中查找相似短信
        
        Args:
            sms_text: 短信文本
            
        Returns:
            tuple: (缓存的结果, 相似度) 如果没有找到则为 (None, -1)
        """
        if not self.vector_enabled or len(self.sms_cache) == 0:
            return None, -1
            
        try:
            query_vector = self.get_embedding(sms_text)
            if query_vector is None:
                logging.warning("无法搜索相似短信：向量为None")
                return None, -1
                
            # 确保向量是正确的形状和类型
            query_vector = np.array([query_vector], dtype=np.float32)
            
            logging.debug(f"搜索向量形状: {query_vector.shape}, 索引大小: {self.index.ntotal}")
            
            # 搜索最相似的短信
            distances, indices = self.index.search(query_vector, 1)
            
            if len(indices) > 0 and len(indices[0]) > 0:
                best_idx = indices[0][0]
                distance = distances[0][0]
                logging.debug(f"找到最佳匹配: idx={best_idx}, distance={distance}, threshold={self.similarity_threshold}")
                
                if distance < self.similarity_threshold:
                    if 0 <= best_idx < len(self.result_cache):
                        return self.result_cache[best_idx], distance
                    else:
                        logging.warning(f"索引越界: {best_idx} 不在结果缓存范围内 (0-{len(self.result_cache)-1})")
                else:
                    logging.debug(f"相似度不足: {distance} > {self.similarity_threshold}")
                
            return None, -1
        except Exception as e:
            import traceback
            logging.error(f"查找相似短信失败: {str(e)}\n{traceback.format_exc()}")
            return None, -1
    
    def cache_result(self, sms_text, result):
        """
        缓存审核结果
        
        Args:
            sms_text: 短信文本
            result: 审核结果
        """
        if not self.vector_enabled:
            return
            
        try:
            vector = self.get_embedding(sms_text)
            if vector is None:
                logging.warning("无法缓存结果：向量为None")
                return
            
            # 打印向量信息用于调试
            logging.debug(f"向量类型: {type(vector)}, 形状: {vector.shape}, 维度: {self.vector_dim}")
            
            # 确保向量是正确的形状和类型
            vector = np.array([vector], dtype=np.float32)
            
            # 打印转换后的向量信息
            logging.debug(f"处理后向量形状: {vector.shape}, dtype: {vector.dtype}")
            
            # 添加到FAISS索引中
            self.index.add(vector)
            self.sms_cache.append(sms_text)
            self.result_cache.append(result)
            
            logging.debug(f"结果已缓存，当前缓存大小: {len(self.sms_cache)}")
        except Exception as e:
            import traceback
            logging.error(f"缓存结果失败: {str(e)}\n{traceback.format_exc()}")
            
    

