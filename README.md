# BBDown Web GUI

🎬 基于 Flask 的 BBDown 网页版图形界面，让B站视频下载更简单！

[[Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[[Flask](https://img.shields.io/badge/Flask-2.0%2B-green.svg)](https://flask.palletsprojects.com/)
[[BBDown](https://img.shields.io/badge/BBDown-Core-orange.svg)](https://github.com/nilaoda/BBDown)
[[License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 功能特性

- 🌐 **友好的Web界面** - 无需命令行，浏览器即可操作
- 📦 **批量下载** - 支持下载整个合集、番剧
- 🎯 **灵活选择** - 可选择画质、编码、分P范围
- 📊 **实时进度** - 实时显示下载进度和日志
- 🔧 **丰富配置** - 支持Cookie、Aria2加速、自定义路径等
- 📱 **响应式设计** - 支持手机、平板等移动设备访问
- 🎨 **美观界面** - 现代化的紫色渐变主题设计

## 📋 系统要求

### 必需依赖
- Python 3.7+
- [BBDown](https://github.com/nilaoda/BBDown) (核心下载工具)

### 可选依赖
- FFmpeg (视频处理)
- Aria2c (多线程下载加速)
- MP4Box (替代混流工具)

## 🚀 快速部署

### 1. 安装 BBDown

首先需要安装 BBDown 核心工具：

```bash
# 方式1：使用 .NET Tool (推荐)
dotnet tool install --global BBDown

# 方式2：下载预编译版本
# 访问 https://github.com/nilaoda/BBDown/releases
# 下载对应系统版本并添加到 PATH
```

### 2. 安装 Python 依赖

```bash
# 克隆项目
git clone https://github.com/chentianqihub/bbdown-web-gui.git
cd bbdown-web-gui

# 安装 Flask
pip install flask

# 或使用 requirements.txt
pip install -r requirements.txt
```

### 3. 运行程序

```bash
python bbdown_web.py
```

程序将在 `http://localhost:5555` 启动

## 🐳 Docker 部署（可选）

创建 `Dockerfile`：

```dockerfile
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
```

构建和运行：

```bash
# 构建镜像
docker build -t bbdown-web-gui .

# 运行容器
docker run -d \
  --name bbdown-web \
  -p 5555:5555 \
  -v ~/Downloads:/downloads \
  bbdown-web-gui
```

## 📖 使用说明

### 基础使用

1. **输入视频地址**
   - 支持 BV号、av号、ep号、ss号
   - 支持完整链接和短链接
   - 支持直接粘贴分享文本

2. **设置Cookie（可选）**
   - 下载大会员视频需要提供Cookie
   - 格式：`SESSDATA=xxxxx` 或完整cookie字符串

3. **选择下载选项**
   - 画质：8K、4K、1080P等
   - 编码：HEVC、AV1、AVC
   - 附加内容：弹幕、字幕、封面

4. **点击开始下载**

### 高级功能

- **分P选择**：支持范围选择如 `1-5`、`3,5,8`
- **API模式**：可选择TV、APP、国际版API
- **文件名模板**：自定义输出文件名格式
- **Aria2加速**：启用多线程下载

## ⚙️ 配置说明

在设置页面可以配置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| BBDown路径 | BBDown可执行文件位置 | `~/.dotnet/tools/BBDown` |
| 默认下载目录 | 视频保存位置 | `~/Downloads/BBDown-Web` |
| FFmpeg路径 | 视频处理工具路径 | 系统默认 |
| Aria2c路径 | 下载加速工具路径 | 系统默认 |
| User-Agent | 自定义浏览器标识 | 随机 |

## 🎯 支持的功能

### 视频类型
- ✅ 普通视频（BV/av号）
- ✅ 番剧/影视（ep/ss号）
- ✅ 合集/分P视频
- ✅ 大会员专享内容（需Cookie）
- ✅ 互动视频

### 下载选项
- ✅ 画质选择（8K/4K/1080P等）
- ✅ 编码选择（HEVC/AV1/AVC）
- ✅ 音视频分离下载
- ✅ 弹幕下载（XML/ASS格式）
- ✅ 字幕下载
- ✅ 封面下载

### 特色功能
- ✅ 批量下载队列
- ✅ 实时日志显示
- ✅ 下载历史记录
- ✅ 自定义文件名模板
- ✅ Aria2多线程加速
- ✅ 解析预览（不下载）

## 📝 文件名模板变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `<videoTitle>` | 视频标题 | "视频标题" |
| `<pageNumber>` | 分P序号 | "1" |
| `<pageTitle>` | 分P标题 | "第一集" |
| `<bvid>` | BV号 | "BV1xx411c7mD" |
| `<aid>` | av号 | "12345678" |
| `<ownerName>` | UP主名称 | "UP主" |
| `<publishDate>` | 发布日期 | "2024-01-01" |

示例：`<videoTitle>/[P<pageNumber>]<pageTitle>`

## 🔧 故障排除

### BBDown 未找到
- 确认BBDown已正确安装
- 检查BBDown路径设置是否正确
- 尝试将BBDown添加到系统PATH

### 下载失败
- 检查网络连接
- 确认视频地址正确
- 大会员视频需要有效Cookie
- 查看日志了解详细错误

### Cookie 获取方法
1. 登录B站网页版
2. 按F12打开开发者工具
3. 切换到Network标签
4. 刷新页面
5. 找到任意请求，查看请求头中的Cookie
6. 复制SESSDATA的值

## 📊 项目结构

```
bbdown-web-gui/
├── bbdown_web.py          # 主程序文件
├── requirements.txt       # Python依赖
├── README.md             # 项目说明
├── LICENSE               # 许可证
└── screenshots/          # 截图目录
    ├── main.png
    ├── download.png
    └── settings.png
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发计划
- [ ] 添加定时下载功能
- [ ] 支持导入/导出下载列表
- [ ] 增加视频预览功能
- [ ] 支持更多视频网站
- [ ] 添加下载限速功能
- [ ] 支持代理设置

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [BBDown](https://github.com/nilaoda/BBDown) - 核心下载引擎
- [Flask](https://flask.palletsprojects.com/) - Web框架
- [Bilibili](https://www.bilibili.com/) - 视频平台

## ⚠️ 免责声明

本项目仅供学习交流使用，请勿用于商业用途。下载的视频请在24小时内删除，如需保存请支持正版。使用本工具产生的一切后果由使用者自行承担。

## 📮 联系方式

- Issues: [GitHub Issues](https://github.com/chentianqihub/bbdown-web-gui/issues)
- Email: your-email@example.com

---

**如果觉得有用，请给个 ⭐ Star 支持一下！**
