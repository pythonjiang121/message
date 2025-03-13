import requests
import json
import pprint
from typing import Tuple

class SignatureCOZE:
    def __init__(self, api_key: str = None):
        """
        初始化 COZE API 客户端
        :param api_key: COZE API密钥，如果不提供则使用默认值
        """
        self.api_key = api_key or "pat_1h7K45g5O4R7RAFBaOAiPfFIk9A1kpJgsDOYx7EO2h0GMQgKtMy5bYkSHX122Quf"
        
        # 定义请求URL
        self.api_url = "https://api.coze.cn/open_api/v2/chat"
        
        # 定义请求头
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Host': 'api.coze.cn',
            'Connection': 'keep-alive'
        }

    def validate_signature(self, signature: str) -> Tuple[bool, str]:
        """
        调用 COZE API 验证签名是否为中性签名
        :param signature: 要验证的签名
        :return: (是否通过验证, 验证消息)
        """
        try:
            # 构建请求数据
            data = {
                "conversation_id": "123",
                "bot_id": "your bot id",  # 需要替换为实际的bot id
                "user": "123333333",
                "query": f"""请判断以下签名是否为中性签名（没有明确主体的签名）。
签名：{signature}

中性签名的判定标准：
1. 没有明确的个人或组织主体（如"温馨提醒"、"通知"等）
2. 通用性表述（如"恭喜发财"、"新年快乐"等）
3. 机构部门格式（如"XX办"、"XX中心"等）
4. 带有中括号、书名号等格式的通用表述（如"【通知】"、"《提醒》"等）
5. 纯功能性描述（如"系统通知"、"服务提醒"等）

请严格按照以下JSON格式返回结果：
{{
    "is_neutral": true/false,  // true表示是中性签名，false表示不是
    "reason": "详细的判断理由"
}}""",
                "stream": False
            }

            # 将数据转换为JSON字符串
            json_data = json.dumps(data)

            # 发送POST请求
            response = requests.post(self.api_url, headers=self.headers, data=json_data)
            response.raise_for_status()
            
            # 解析响应
            try:
                result = response.json()
                content = result.get("reply", "")
                validation_result = json.loads(content)
                return (not validation_result["is_neutral"], 
                       "审核通过" if not validation_result["is_neutral"] else validation_result["reason"])
            except json.JSONDecodeError:
                return False, "API返回格式错误"
            except KeyError:
                return False, "API响应格式不正确"

        except requests.RequestException as e:
            return False, f"API请求失败: {str(e)}"
        except Exception as e:
            return False, f"验证过程出错: {str(e)}"

# 使用示例
if __name__ == "__main__":
    validator = SignatureCOZE()
    
    # 测试一些签名
    test_signatures = [
        "恭喜发财",
        "市燃气办",
        "温馨提醒",
        "张三",
        "李四商店",
        "【通知】",
        "《提醒》",
        "中国移动",
        "某某银行"
    ]
    
    print("开始签名审核测试...")
    print("=" * 50)
    
    for sig in test_signatures:
        result, message = validator.validate_signature(sig)
        pprint.pprint({
            "签名": sig,
            "结果": "通过" if result else "不通过",
            "原因": message
        })
        print("-" * 50) 