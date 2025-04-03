#!/bin/bash
set -e

# 打印欢迎信息
echo "============================================="
echo "      短信审核系统 - Docker版本启动         "
echo "============================================="
echo "启动时间: $(date)"
echo

# 运行 API 服务
echo "以API服务模式运行 (checkAPI.py)..."
exec python checkAPI.py 