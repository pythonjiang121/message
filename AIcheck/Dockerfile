FROM hub.n2m.cn/library/python:3.10-slim
# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
apt-get update && apt-get install -y --no-install-recommends \
build-essential \
zsh \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

# 复制依赖文件和安装脚本
COPY requirements.txt install_deps.sh entrypoint.sh ./

# 添加执行权限并运行安装脚本
RUN chmod +x install_deps.sh && ./install_deps.sh

# 复制应用代码
COPY checkAPI.py ai_check.py ai_audit_prompt.py ./

# 创建日志和数据目录
RUN mkdir -p logs data

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV SHELL=/bin/zsh

# 设置入口点
ENTRYPOINT ["/app/entrypoint.sh"]

# 暴露端口
EXPOSE 8000

RUN chmod +x /app/entrypoint.sh 