#!/bin/bash
# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 显示标题
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}   SMS审核系统 - Docker依赖安装   ${NC}"
echo -e "${GREEN}====================================${NC}"

# 安装生产依赖
echo -e "${YELLOW}安装生产依赖...${NC}"
pip install --no-cache-dir -r requirements.txt

# 创建必要的目录
echo -e "${YELLOW}创建必要的目录...${NC}"
mkdir -p data logs

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}   依赖安装完成!   ${NC}"
echo -e "${GREEN}====================================${NC}" 