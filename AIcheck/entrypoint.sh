#!/bin/bash
set -e

# 打印欢迎信息
echo "============================================="
echo "      短信审核系统 - Docker版本启动         "
echo "============================================="
echo "启动时间: $(date)"
echo

# 创建日志目录
mkdir -p /app/logs

# 在后台启动余额监控服务
echo "启动余额监控服务..."
nohup python balance_monitor.py --interval 86400 --threshold 10.0 > /app/logs/balance_monitor.log 2>&1 &
echo "余额监控已在后台启动，每24小时检查一次，低于10元人民币时发送企业微信告警"
echo "余额监控日志: /app/logs/balance_monitor.log"

# 启动API服务
echo "启动短信审核API服务..."
exec python checkAPI.py 