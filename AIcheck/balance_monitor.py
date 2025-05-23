#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import logging
import schedule
import sys
import os
from ai_check import AIAuditor

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)



# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('balance_monitor.log'),
        logging.StreamHandler()
    ]
)

class BalanceMonitor:
    def __init__(self, check_interval=3600, threshold=10.0):
        """
        初始化余额监控器
        
        Args:
            check_interval: 检查间隔（秒）
            threshold: 余额告警阈值（美元）
        """
        self.check_interval = check_interval
        self.ai_auditor = AIAuditor()
        
        # 设置告警阈值
        self.ai_auditor.balance_alert_threshold = threshold
        
        logging.info(f"余额监控器已初始化，检查间隔: {check_interval}秒，告警阈值: ${threshold}")
    
    def check_balance(self):
        """
        检查API余额
        """
        try:
            logging.info("开始检查DeepSeek API余额")
            # 通知AIAuditor这是定时检查，允许发送告警
            balance_info = self.ai_auditor.check_api_balance(is_scheduled_check=True)
            
            if "error" not in balance_info:
                if "is_available" in balance_info and "balance_infos" in balance_info and len(balance_info["balance_infos"]) > 0:
                    balance_data = balance_info["balance_infos"][0]
                    currency = balance_data["currency"]
                    if "total_balance" in balance_data:
                        balance = float(balance_data["total_balance"])
                        if currency == "CNY":
                            logging.info(f"当前余额: ¥{balance:.2f}")
                        else:
                            logging.info(f"当前账户货币不是人民币，无法进行告警（当前货币: {currency}）")
                else:
                    logging.warning(f"余额信息格式异常: {balance_info}")
            else:
                logging.error(f"获取余额信息失败: {balance_info['error']}")
            
            return balance_info
        except Exception as e:
            logging.error(f"检查余额过程中发生错误: {str(e)}")
            return {"error": str(e)}
    
    def start_monitor(self):
        """
        启动监控
        """
        logging.info("正在启动余额监控器...")
        
        # 立即执行一次检查
        self.check_balance()
        
        # 设置定时任务
        schedule.every(self.check_interval).seconds.do(self.check_balance)
        
        logging.info(f"余额监控器已启动，将每 {self.check_interval} 秒检查一次")
        
        # 持续运行定时任务
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("余额监控器已停止")
        except Exception as e:
            logging.error(f"余额监控器运行出错: {str(e)}")

def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='DeepSeek API余额监控工具')
    parser.add_argument('--interval', type=int, default=86400, help='检查间隔（秒），默认为86400秒（24小时）')
    parser.add_argument('--threshold', type=float, default=10.0, help='余额告警阈值（元），默认为10.0元')
    args = parser.parse_args()
    
    monitor = BalanceMonitor(check_interval=args.interval, threshold=args.threshold)
    monitor.start_monitor()

if __name__ == "__main__":
    main() 