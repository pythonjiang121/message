#!/bin/zsh

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 显示标题
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}   SMS Audit API 部署脚本   ${NC}"
echo -e "${GREEN}====================================${NC}"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装，请先安装Docker${NC}"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose未安装，请先安装Docker Compose${NC}"
    exit 1
fi

# 创建必要的目录
echo -e "${YELLOW}创建必要的目录...${NC}"
mkdir -p data logs

# 停止并移除现有容器
echo -e "${YELLOW}停止并移除现有容器...${NC}"
docker-compose down

# 构建新镜像
echo -e "${YELLOW}构建Docker镜像...${NC}"
docker-compose build

# 启动服务
echo -e "${YELLOW}启动服务...${NC}"
docker-compose up -d

# 检查服务是否成功启动
if [ $? -eq 0 ]; then
    echo -e "${GREEN}服务已成功启动!${NC}"
    echo -e "${GREEN}API服务地址: http://localhost:8000${NC}"
    echo -e "${GREEN}查看日志: docker-compose logs -f${NC}"
else
    echo -e "${RED}服务启动失败，请检查日志${NC}"
    docker-compose logs
    exit 1
fi 