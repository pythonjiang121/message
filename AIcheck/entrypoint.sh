#!/bin/bash
set -e

# 打印欢迎信息
echo "============================================="
echo "      短信审核系统 - 启动         "
echo "============================================="
echo "启动时间: $(date)"
echo

# 创建日志目录
mkdir -p logs

# 在后台启动余额监控服务
echo "启动余额监控服务..."
nohup python balance_monitor.py > logs/balance_monitor.log 2>&1 &
echo "余额监控已在后台启动，使用全局配置参数"
echo "余额监控日志: logs/balance_monitor.log"

# 启动API服务
echo "启动短信审核API服务..."
exec python checkAPI.py 