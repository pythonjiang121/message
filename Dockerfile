FROM hub.n2m.cn/library/python:3.8-slim

# ubuntu换源
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 换为国内源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set install.trusted-host mirrors.aliyun.com

# 系统更新和安装基础工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*


# 设置工作目录
WORKDIR /app

# 复制并安装依赖
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . /app

# 创建必要的目录
RUN mkdir -p logs data

# 清理不必要的文件
RUN find . -type d -name "__pycache__" -exec rm -rf {} +
RUN find . -type f -name "*.pyc" -delete

# 设置入口点脚本权限
RUN chmod +x entrypoint.sh

# 创建一个非root用户运行应用
RUN groupadd -r smsaudit && useradd -r -g smsaudit smsaudit
RUN chown -R smsaudit:smsaudit /app
USER smsaudit

# 设置容器入口点
ENTRYPOINT ["/app/entrypoint.sh"] 