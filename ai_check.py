# ai_audit.py

import requests
import json
from typing import Dict, Tuple, List
import logging
from datetime import datetime
import re
from openai import OpenAI


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
        
        # 系统提示词
        self.system_prompt = """你是一个专业的短信内容审核专家，负责评估短信是否符合监管要求和行业规范。

评估标准：
1. 链接风险：
- 短链接或可疑域名
- 紧急催促用语
- 不合理时效限制

2. 营销话术：
- 诱导性词语(首批/限量等)
- 过高金额承诺
- 制造紧迫感

3. 业务合规：
- 威胁性通知
- 发送方身份
- 管制敏感产品

4. 内容真实性：
- 夸大虚假宣传
- 迷信伪科学
- 优惠真实性

5. 违规内容：
- 涉黄涉赌
- 涉诈涉暴
- 涉政涉恐
- 涉毒涉敏感信息
- 高回报/免费获利

请以JSON格式输出你的判断：
{
    "should_pass": true/false,
    "reasons": ["具体理由1", "具体理由2"]
}"""

    def audit_sms(self, signature: str, content: str, business_type: str, 
                 rule_score: float, rule_reason: str) -> Tuple[bool, Dict]:
        """
        对单条短信进行AI审核
        
        Args:
            signature: 短信签名
            content: 短信内容
            business_type: 业务类型
            rule_score: 规则审核得分
            rule_reason: 规则审核原因
            
        Returns:
            Tuple[bool, Dict]: (是否通过审核, 审核结果详情)
        """
        try:
            # 构建用户提示词
            user_prompt = f"""请审核以下短信内容：

签名：【{signature}】
内容：{content}
业务类型：{business_type}
规则审核分数：{rule_score}
规则审核原因：{rule_reason}

请仔细评估短信内容是否符合规范，重点关注以下风险点：

1. 链接风险：
- 短链接或可疑域名
- 紧急催促用语
- 不合理时效限制

2. 营销话术：
- 诱导性词语(首批/限量等)
- 过高金额承诺
- 制造紧迫感

3. 业务合规：
- 威胁性通知
- 发送方身份
- 管制敏感产品

4. 内容真实性：
- 夸大虚假宣传
- 迷信伪科学
- 优惠真实性

5. 违规内容：
- 涉黄涉赌
- 涉诈涉暴
- 涉政涉恐
- 涉毒涉敏感信息
- 高回报/免费获利

请严格评估以上风险点,发现任一风险即判定不通过。
"""

            # 构建请求数据
            payload = {
                "model": "deepseek-chat",  # 使用适当的模型名称
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
            # 接受请求
            if response.status_code == 200:
                result = response.json()
                ai_response = result["choices"][0]["message"]["content"]
                
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
                return audit_result["should_pass"], audit_result
            else:
                logging.error(f"API调用失败: {response.status_code}, {response.text}")
                return False, {"error": f"API调用失败: {response.status_code}"}

        except Exception as e:
            logging.error(f"AI审核过程出错: {str(e)}")
            return False, {"error": str(e)}

    def batch_audit(self, sms_list: List[Dict]) -> List[Dict]:
        """
        批量审核短信
        
        Args:
            sms_list: 短信列表，每个元素包含 signature, content, business_type, rule_score, rule_reason
            
        Returns:
            List[Dict]: 审核结果列表，每个元素包含 sms, passed, details
        """
        results = []
        total = len(sms_list)
        
        logging.info(f"开始批量审核 {total} 条短信")
        
        for i, sms in enumerate(sms_list):
            try:
                # 记录进度
                if i % 1 == 0:
                    logging.info(f"正在处理: {i+1}/{total}")
                    
                # 调用单条审核方法
                passed, details = self.audit_sms(
                    sms["signature"],
                    sms["content"],
                    sms["business_type"],
                    sms["rule_score"],
                    sms["rule_reason"]
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
        
        logging.info(f"批量审核完成，共处理 {len(results)} 条短信")
        return results

