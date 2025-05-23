import requests
import json
from typing import Dict, Tuple, List
import logging
import re
from ai_audit_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, BUSINESS_SPECIFIC_RULES


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
        
        # 企业微信机器人配置
        self.wecom_webhook = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=30ffc3b2-da6e-421b-9b24-b3d3cc51f8d3"
        
        # 余额告警阈值，单位：人民币
        self.balance_alert_threshold = 10.0
        
        # 上次发送告警的时间，避免频繁告警
        self.last_alert_time = 0
        # 告警间隔，默认4小时
        self.alert_interval = 4 * 60 * 60  # 4小时，单位：秒
        


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

    def check_api_balance(self, is_scheduled_check=False) -> Dict:
        """
        查询DeepSeek API的余额和使用情况
        
        Args:
            is_scheduled_check: 是否为定时检查，只有定时检查才会触发告警，默认为False
            
        Returns:
            Dict: API余额和使用情况信息
        """
        try:
            # DeepSeek API余额查询接口
            balance_endpoint = "https://api.deepseek.com/user/balance"
            
            # 发送请求
            response = requests.get(
                balance_endpoint,
                headers=self.headers
            )
            
            if response.status_code == 200:
                balance_info = response.json()
                logging.info(f"API余额查询成功: {balance_info}")
                
                # 只有定时检查才会触发告警
                if is_scheduled_check:
                    self._check_balance_alert(balance_info, is_scheduled_check)
                
                return balance_info
            else:
                error_msg = f"API余额查询失败: {response.status_code}"
                if hasattr(response, 'text'):
                    error_msg += f", {response.text}"
                logging.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            logging.error(f"查询API余额出错: {str(e)}")
            return {"error": str(e)}
    
    def _check_balance_alert(self, balance_info: Dict, is_scheduled_check=False) -> None:
        """
        检查余额是否低于阈值，如果是则发送企业微信告警
        
        Args:
            balance_info: API余额信息
            is_scheduled_check: 是否为定时检查，只有定时检查才会触发告警
        """
        try:
            # 非定时检查不发送告警
            if not is_scheduled_check:
                return
                
            # 提取余额信息
            balance = None
            currency = ""
            
            # 根据DeepSeek API文档的格式解析
            if "is_available" in balance_info and "balance_infos" in balance_info:
                if balance_info["is_available"] and len(balance_info["balance_infos"]) > 0:
                    # 获取第一个货币的余额信息
                    balance_data = balance_info["balance_infos"][0]
                    currency = balance_data["currency"]
                    
                    # 获取总余额
                    if "total_balance" in balance_data:
                        balance = float(balance_data["total_balance"])
            
            if balance is None:
                logging.warning("无法从响应中提取余额信息")
                return
            
            # 只处理人民币账户，忽略美元账户
            if currency != "CNY":
                logging.info(f"当前账户货币不是人民币，跳过告警检查（当前货币: {currency}）")
                return
                
            # 设置告警阈值（10元人民币）
            threshold = 10.0
                
            import time
            current_time = time.time()
            
            # 如果余额低于阈值且距离上次告警时间超过间隔，则发送告警
            if balance < threshold and current_time - self.last_alert_time > self.alert_interval:
                logging.info(f"余额低于阈值，当前余额: ¥{balance:.2f}，阈值: ¥{threshold:.2f}")
                
                # 格式化告警消息
                alert_msg = (
                    f"⚠️ **DeepSeek API余额告警**\n\n"
                    f"当前余额: ¥{balance:.2f}\n"
                    f"告警阈值: ¥{threshold:.2f}\n\n"
                )
                
                # 添加赠金和充值余额信息
                if "granted_balance" in balance_info["balance_infos"][0] and "topped_up_balance" in balance_info["balance_infos"][0]:
                    granted = float(balance_info["balance_infos"][0]["granted_balance"])
                    topped_up = float(balance_info["balance_infos"][0]["topped_up_balance"])
                    
                    alert_msg += f"充值余额: ¥{topped_up:.2f}\n"
                    alert_msg += f"赠金余额: ¥{granted:.2f}\n\n"
                
                alert_msg += "请及时充值，以免影响服务!"
                
                # 发送企业微信告警
                self._send_wecom_alert(alert_msg)
                
                # 更新上次告警时间
                self.last_alert_time = current_time
                
                logging.info(f"余额告警已发送，当前余额: ¥{balance:.2f}")
            else:
                if balance < threshold:
                    logging.info(f"余额低于阈值，但距离上次告警时间未超过{self.alert_interval/3600:.1f}小时，不发送告警")
                else:
                    logging.info(f"余额正常，当前余额: ¥{balance:.2f}")
        except Exception as e:
            logging.error(f"余额告警检查失败: {str(e)}")
    
    def _send_wecom_alert(self, message: str) -> None:
        """
        发送企业微信告警
        
        Args:
            message: 告警消息
        """
        try:
            # 构建告警消息
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": message
                }
            }
            
            # 发送请求
            response = requests.post(
                self.wecom_webhook,
                headers={"Content-Type": "application/json"},
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    logging.info("企业微信告警发送成功")
                else:
                    logging.error(f"企业微信告警发送失败: {result}")
            else:
                logging.error(f"企业微信告警发送失败，状态码: {response.status_code}")
        except Exception as e:
            logging.error(f"发送企业微信告警失败: {str(e)}")
            
    # 添加获取token使用统计的方法
    def get_token_usage_stats(self) -> Dict:
        """
        获取当前实例的token使用统计
        
        Returns:
            Dict: token使用统计信息
        """
        return {
            "total_tokens_used": self.total_tokens_used,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "average_cost_estimate": self.total_tokens_used * 0.0001  # 假设每千tokens的成本为0.1人民币
        }

