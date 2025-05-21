FROM hub.n2m.cn/library/python:3.10-slim
# 设置工作目录
WORKDIR /app

# 复制依赖文件和安装脚本
COPY requirements.txt entrypoint.sh ./

# 使用清华镜像源安装 Python 依赖
# RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple/ -r requirements.txt

# 使用阿里云镜像源安装 Python 依赖
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

#正常安装依赖
# RUN pip install --no-cache-dir -r requirements.txt


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