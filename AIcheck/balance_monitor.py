#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import logging
import schedule
import sys
import os
from ai_check import AIAuditor, BALANCE_CHECK_INTERVAL, BALANCE_ALERT_THRESHOLD

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 创建独立的日志记录器
balance_logger = logging.getLogger('balance_monitor')
balance_logger.setLevel(logging.INFO)
# 禁用向父日志记录器传播，避免日志重复
balance_logger.propagate = False

# 创建日志目录
os.makedirs('logs', exist_ok=True)

# 创建文件处理器
file_handler = logging.FileHandler('logs/balance_monitor.log')
file_handler.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 创建格式器
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加处理器到日志记录器
balance_logger.addHandler(file_handler)
balance_logger.addHandler(console_handler)

class BalanceMonitor:
    def __init__(self, check_interval=None, threshold=None):
        """
        初始化余额监控器
        
        Args:
            check_interval: 检查间隔（秒），如果为None则使用全局配置
            threshold: 余额告警阈值（人民币元），如果为None则使用全局配置
        """
        # 使用参数值或默认全局配置
        self.check_interval = check_interval if check_interval is not None else BALANCE_CHECK_INTERVAL
        self.ai_auditor = AIAuditor()
        
        # 设置告警阈值，使用参数值或默认全局配置
        threshold_value = threshold if threshold is not None else BALANCE_ALERT_THRESHOLD
        self.ai_auditor.balance_alert_threshold = threshold_value
        
        balance_logger.info(f"余额监控器已初始化，检查间隔: {self.check_interval}秒，告警阈值: ¥{threshold_value}")
    
    def check_balance(self):
        """
        检查API余额
        """
        try:
            balance_logger.info("开始检查DeepSeek API余额")
            # 通知AIAuditor这是定时检查，允许发送告警
            balance_info = self.ai_auditor.check_api_balance(is_scheduled_check=True)
            
            if "error" not in balance_info:
                if "is_available" in balance_info and "balance_infos" in balance_info:
                    # 查找人民币余额
                    cny_balance = None
                    for balance_data in balance_info["balance_infos"]:
                        if balance_data["currency"] == "CNY" and "total_balance" in balance_data:
                            cny_balance = float(balance_data["total_balance"])
                            balance_logger.info(f"当前人民币余额: ¥{cny_balance:.2f}")
                            
                            # 检查余额是否低于阈值
                            if cny_balance < self.ai_auditor.balance_alert_threshold:
                                balance_logger.warning(f"余额警告: 当前余额 ¥{cny_balance:.2f} 低于警告阈值 ¥{self.ai_auditor.balance_alert_threshold:.2f}")
                            break
                    
                    if cny_balance is None:
                        balance_logger.warning("未找到人民币余额信息")
                else:
                    balance_logger.warning(f"余额信息格式异常: {balance_info}")
            else:
                balance_logger.error(f"获取余额信息失败: {balance_info['error']}")
            
            return balance_info
        except Exception as e:
            balance_logger.error(f"检查余额过程中发生错误: {str(e)}")
            return {"error": str(e)}
    
    def start_monitor(self):
        """
        启动监控
        """
        balance_logger.info("正在启动余额监控器...")
        
        # 立即执行一次检查
        self.check_balance()
        
        # 设置定时任务
        schedule.every(self.check_interval).seconds.do(self.check_balance)
        
        balance_logger.info(f"余额监控器已启动，将每 {self.check_interval} 秒检查一次")
        
        # 持续运行定时任务
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            balance_logger.info("余额监控器已停止")
        except Exception as e:
            balance_logger.error(f"余额监控器运行出错: {str(e)}")

def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='DeepSeek API余额监控工具')
    parser.add_argument('--interval', type=int, default=BALANCE_CHECK_INTERVAL, 
                        help=f'检查间隔（秒），默认为{BALANCE_CHECK_INTERVAL}秒（{BALANCE_CHECK_INTERVAL/3600}小时）')
    parser.add_argument('--threshold', type=float, default=BALANCE_ALERT_THRESHOLD, 
                        help=f'余额告警阈值（元），默认为{BALANCE_ALERT_THRESHOLD}元')
    args = parser.parse_args()
    
    monitor = BalanceMonitor(check_interval=args.interval, threshold=args.threshold)
    monitor.start_monitor()

if __name__ == "__main__":
    main() 