# 运行环境
FROM python:3.9-slim

# 设置环境变量
ENV DOTNET_ROOT=/root/.dotnet
ENV PATH=$PATH:$DOTNET_ROOT:$DOTNET_ROOT/tools

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ffmpeg \
    aria2 \
    ca-certificates \
    libicu-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 .NET SDK 和 BBDown
RUN wget https://dot.net/v1/dotnet-install.sh \
    && chmod +x dotnet-install.sh \
    && ./dotnet-install.sh \
    && rm dotnet-install.sh \
    && $DOTNET_ROOT/dotnet tool install --global BBDown

# 设置工作目录
WORKDIR /app

# 创建下载目录
RUN mkdir -p /root/Downloads/BBDown-Web

# 先复制 requirements.txt 文件
COPY requirements.txt .

# 升级 pip 并安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY bbdown_web.py .    

# 暴露端口
EXPOSE 5555

# 启动命令
CMD ["python", "-u", "bbdown_web.py"]
