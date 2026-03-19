FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口（对应你截图中的 Container Port 80）
EXPOSE 80

# 启动命令
CMD ["python", "app.py"]