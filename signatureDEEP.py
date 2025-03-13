import requests
import json
import os
from typing import Tuple

class SignatureCOZE:
    def __init__(self, api_key: str = None):
        """
        初始化 COZE API 客户端
        :param api_key: COZE API密钥，如果不提供则从环境变量COZE_API_KEY获取
        """
        self.api_key = api_key or os.getenv('COZE_API_KEY')
        if not self.api_key:
            raise ValueError("COZE API key is required. Please provide it or set COZE_API_KEY environment variable.")
        
        self.api_url = "https://api.coze.cn/v1/chat/completions"  # COZE API 端点
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def validate_signature(self, signature: str) -> Tuple[bool, str]:
        """
        调用 COZE API 验证签名是否为中性签名
        :param signature: 要验证的签名
        :return: (是否通过验证, 验证消息)
        """
        try:
            # 构建提示信息
            prompt = f"""请判断以下签名是否为中性签名（没有明确主体的签名）。
签名：{signature}

中性签名的特征：
1. 没有明确的个人或组织主体
2. 通用性表述（如：温馨提醒、恭喜发财等）
3. 机构部门格式（如：XX办、XX中心等）
4. 带有中括号、书名号等格式的通用表述

请只返回如下JSON格式：
{{
    "is_neutral": true/false,
    "reason": "判断原因"
}}"""

            # 准备请求数据
            payload = {
                "model": "coze-bot",  # 使用适当的模型名称
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }

            # 发送请求
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                try:
                    validation_result = json.loads(content)
                    return (not validation_result["is_neutral"], 
                           "审核通过" if not validation_result["is_neutral"] else validation_result["reason"])
                except json.JSONDecodeError:
                    return False, "API返回格式错误"
            else:
                return False, "API响应无效"

        except requests.RequestException as e:
            return False, f"API请求失败: {str(e)}"
        except Exception as e:
            return False, f"验证过程出错: {str(e)}"

# 使用示例
if __name__ == "__main__":
    # 从环境变量获取API密钥
    coze_validator = SignatureCOZE()
    
    # 测试一些签名
    test_signatures = [
        "恭喜发财",
        "市燃气办",
        "温馨提醒",
        "张三",
        "李四商店"
    ]
    
    for sig in test_signatures:
        result, message = coze_validator.validate_signature(sig)
        print(f"签名: {sig}")
        print(f"结果: {'通过' if result else '不通过'}")
        print(f"原因: {message}")
        print("-" * 30) 