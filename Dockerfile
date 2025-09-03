FROM python:3.9-slim

# 安装依赖
RUN apt-get update && apt-get install -y \
    wget \
    ffmpeg \
    aria2 \
    && rm -rf /var/lib/apt/lists/*

# 安装 .NET 和 BBDown
RUN wget https://dot.net/v1/dotnet-install.sh \
    && chmod +x dotnet-install.sh \
    && ./dotnet-install.sh --channel 6.0 \
    && /root/.dotnet/dotnet tool install --global BBDown

# 设置工作目录
WORKDIR /app

# 复制文件
COPY bbdown_web.py .
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV PATH="/root/.dotnet/tools:${PATH}"

# 暴露端口
EXPOSE 5555

# 创建下载目录
RUN mkdir -p /downloads

# 启动命令
CMD ["python", "bbdown_web.py"]
