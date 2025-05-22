#!/bin/bash 
# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 显示标题
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}   SMS Check API 部署脚本   ${NC}"
echo -e "${GREEN}====================================${NC}"

# 检查Docker是否安装
if ! command -v sudo docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装，请先安装Docker${NC}"
    exit 1
fi

# 定义容器名称和镜像名称
CONTAINER_NAME="sms-check-api"
IMAGE_NAME="sms-check-api:latest"

# 创建必要的目录
echo -e "${YELLOW}创建必要的目录...${NC}"
mkdir -p data logs

# 停止并移除现有容器
echo -e "${YELLOW}停止并移除现有容器...${NC}"
sudo docker stop $CONTAINER_NAME 2>/dev/null || true
sudo docker rm $CONTAINER_NAME 2>/dev/null || true

# 构建新镜像
echo -e "${YELLOW}构建Docker镜像...${NC}"
sudo docker build -t $IMAGE_NAME .

# 检查构建是否成功
if [ $? -ne 0 ]; then
    echo -e "${RED}镜像构建失败，请检查Dockerfile和网络连接${NC}"
    exit 1
fi

# 启动服务
echo -e "${YELLOW}启动服务...${NC}"
sudo docker run -d --name $CONTAINER_NAME \
    -p 8000:8000 \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/logs:/app/logs" \
    -e TZ=Asia/Shanghai \
    --restart unless-stopped \
    $IMAGE_NAME

# 检查服务是否成功启动
if [ $? -eq 0 ]; then
    echo -e "${GREEN}服务已成功启动!${NC}"
    echo -e "${GREEN}API服务地址: http://localhost:8000${NC}"
    echo -e "${GREEN}查看日志: docker logs -f $CONTAINER_NAME${NC}"
    
    # 等待服务完全启动
    echo -e "${YELLOW}等待服务完全启动...${NC}"
    sleep 5
    
    # 测试API是否可访问
    echo -e "${YELLOW}测试API服务...${NC}"
    if curl -s http://localhost:8000 &> /dev/null; then
        echo -e "${GREEN}API服务已成功启动并可访问!${NC}"
    else
        echo -e "${YELLOW}警告: API服务可能未完全启动，请稍后再尝试访问${NC}"
    fi
else
    echo -e "${RED}服务启动失败，请检查日志${NC}"
    sudo docker logs $CONTAINER_NAME 2>/dev/null || echo "无法获取容器日志"
    exit 1
fi 