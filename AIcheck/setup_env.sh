#!/bin/zsh

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 显示标题
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}   SMS审核系统 - 环境设置脚本   ${NC}"
echo -e "${GREEN}====================================${NC}"

# 检查Python版本
echo -e "${YELLOW}检查Python版本...${NC}"
PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
echo -e "当前Python版本: ${GREEN}$PYTHON_VERSION${NC}"

# 创建虚拟环境（如果不存在）
if [ ! -d " ./sms_check_env" ]; then
    echo -e "${YELLOW}创建虚拟环境...${NC}"
    python3 -m venv ./sms_check_env
    echo -e "${GREEN}虚拟环境已创建${NC}"
else
    echo -e "${GREEN}虚拟环境已存在${NC}"
fi

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source ./sms_check_env/bin/activate

# 升级pip
echo -e "${YELLOW}升级pip...${NC}"
pip install --upgrade pip

# 安装生产依赖
echo -e "${YELLOW}安装生产依赖...${NC}"
pip install -r requirements.txt

# 询问是否安装开发依赖
read "REPLY?是否安装开发依赖? (y/n) "
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}安装开发依赖...${NC}"
    pip install -r requirements-dev.txt
    
    # 设置pre-commit
    echo -e "${YELLOW}设置pre-commit...${NC}"
    pre-commit install
fi

# 创建必要的目录
echo -e "${YELLOW}创建必要的目录...${NC}"
mkdir -p ./data ./logs

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}   环境设置完成!   ${NC}"
echo -e "${GREEN}====================================${NC}"
echo -e "使用方式:"
echo -e "1. 激活环境: ${YELLOW}source ./sms_check_env/bin/activate${NC}"
echo -e "2. 运行API: ${YELLOW}python checkAPI.py${NC}"
echo -e "3. 运行测试: ${YELLOW}pytest${NC}" 