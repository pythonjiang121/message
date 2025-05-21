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

# 启动API服务
echo "Starting SMS Audit API service..."
exec python checkAPI.py 