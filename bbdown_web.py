from flask import Flask, request, render_template_string, jsonify
import os
import subprocess
import threading
import queue
import time
from datetime import datetime
import re
from pathlib import Path

app = Flask(__name__)

# 版本信息
APP_VERSION = "1.2.3"

# 全局变量存储下载任务
download_queue = queue.Queue()
download_status = {}
download_history = []

# 默认下载目录
DEFAULT_WORK_DIR = os.path.expanduser("~/Downloads/BBDown-Web")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BBDown Web GUI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            padding-bottom: 60px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .input-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #333;
        }
        input[type="text"], input[type="password"], input[type="number"], select, textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        textarea {
            resize: vertical;
            min-height: 60px;
        }
        .checkbox-group {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 15px;
        }
        .checkbox-group label {
            display: flex;
            align-items: center;
            font-weight: normal;
            margin-bottom: 0;
        }
        .checkbox-group input[type="checkbox"] {
            margin-right: 5px;
        }
        .button-group {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        button {
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
        }
        button:hover {
            background: #5a67d8;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .secondary-btn {
            background: #48bb78;
        }
        .secondary-btn:hover {
            background: #38a169;
        }
        .danger-btn {
            background: #f56565;
        }
        .danger-btn:hover {
            background: #e53e3e;
        }
        .info-btn {
            background: #4299e1;
        }
        .info-btn:hover {
            background: #3182ce;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e2e8f0;
        }
        .tab {
            padding: 10px 20px;
            background: none;
            border: none;
            color: #718096;
            cursor: pointer;
            font-size: 16px;
            border-bottom: 2px solid transparent;
            margin-bottom: -2px;
        }
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .status-item {
            padding: 15px;
            border: 1px solid #e2e8f0;
            border-radius: 5px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .status-downloading {
            border-left: 4px solid #4299e1;
        }
        .status-completed {
            border-left: 4px solid #48bb78;
        }
        .status-failed {
            border-left: 4px solid #f56565;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-fill {
            height: 100%;
            background: #48bb78;
            transition: width 0.3s;
        }
        .log-output {
            background: #1a202c;
            color: #a0aec0;
            padding: 15px;
            border-radius: 5px;
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 'Courier New', monospace;
            font-size: 11px;
            line-height: 1.5;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        /* 日志级别颜色 */
        .log-timestamp { color: #718096; }
        .log-info { color: #63b3ed; }
        .log-success { color: #68d391; font-weight: 500; }
        .log-warning { color: #fbd38d; }
        .log-error { color: #fc8181; font-weight: 500; }
        .log-debug { color: #b794f4; }
        .log-progress { color: #4fd1c5; font-weight: 500; }
        .log-title { color: #f6ad55; font-weight: bold; }
        .log-separator { color: #4a5568; }
        
        .grid-2 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        .advanced-options {
            display: none;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
        }
        .toggle-advanced {
            color: #667eea;
            cursor: pointer;
            text-decoration: underline;
            margin-bottom: 15px;
            display: inline-block;
        }
        .info-box {
            background: #f0f9ff;
            border-left: 4px solid #4299e1;
            padding: 12px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .info-box p {
            margin: 0;
            color: #2c5282;
            font-size: 14px;
        }
        .help-text {
            font-size: 12px;
            color: #718096;
            margin-top: 5px;
            line-height: 1.4;
        }
        .help-text code {
            background: #f7fafc;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 11px;
            color: #4a5568;
        }
        .settings-section {
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e2e8f0;
        }
        .settings-section h3 {
            color: #4a5568;
            margin-bottom: 15px;
            font-size: 18px;
        }
        .settings-section:last-child {
            border-bottom: none;
        }
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(26, 32, 44, 0.9);
            color: #a0aec0;
            padding: 10px;
            text-align: center;
            font-size: 12px;
            backdrop-filter: blur(10px);
        }
        .footer a {
            color: #63b3ed;
            text-decoration: none;
        }
        .footer a:hover {
            text-decoration: underline;
        }
        
        /* 自定义通知样式 */
        .notification-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .notification {
            background: white;
            padding: 16px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 300px;
            max-width: 400px;
            animation: slideIn 0.3s ease-out;
            position: relative;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        
        .notification.removing {
            animation: slideOut 0.3s ease-in;
        }
        
        .notification-icon {
            width: 24px;
            height: 24px;
            flex-shrink: 0;
        }
        
        .notification.success {
            border-left: 4px solid #48bb78;
        }
        
        .notification.error {
            border-left: 4px solid #f56565;
        }
        
        .notification.info {
            border-left: 4px solid #4299e1;
        }
        
        .notification.warning {
            border-left: 4px solid #f6ad55;
        }
        
        .notification-content {
            flex: 1;
        }
        
        .notification-title {
            font-weight: 600;
            margin-bottom: 4px;
            color: #2d3748;
        }
        
        .notification-message {
            color: #718096;
            font-size: 14px;
        }
        
        .notification-close {
            position: absolute;
            top: 8px;
            right: 8px;
            background: none;
            border: none;
            color: #a0aec0;
            cursor: pointer;
            font-size: 18px;
            line-height: 1;
            padding: 4px;
        }
        
        .notification-close:hover {
            color: #4a5568;
        }
        
        /* 自定义确认对话框 */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s, visibility 0.3s;
        }
        
        .modal-overlay.active {
            opacity: 1;
            visibility: visible;
        }
        
        .modal {
            background: white;
            border-radius: 12px;
            padding: 24px;
            max-width: 400px;
            width: 90%;
            transform: scale(0.9);
            transition: transform 0.3s;
        }
        
        .modal-overlay.active .modal {
            transform: scale(1);
        }
        
        .modal-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #2d3748;
        }
        
        .modal-message {
            color: #718096;
            margin-bottom: 20px;
            line-height: 1.5;
        }
        
        .modal-buttons {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        
        .modal-button {
            padding: 8px 16px;
            border-radius: 6px;
            border: none;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .modal-button.primary {
            background: #667eea;
            color: white;
        }
        
        .modal-button.primary:hover {
            background: #5a67d8;
        }
        
        .modal-button.secondary {
            background: #e2e8f0;
            color: #4a5568;
        }
        
        .modal-button.secondary:hover {
            background: #cbd5e0;
        }
        
        @media (max-width: 768px) {
            .header h1 { font-size: 1.8em; }
            .button-group { flex-direction: column; }
            button { width: 100%; }
            .notification-container {
                left: 20px;
                right: 20px;
                top: 10px;
            }
            .notification {
                min-width: auto;
                max-width: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 BBDown Web GUI</h1>
            <p>B站视频下载工具网页版</p>
        </div>

        <div class="card">
            <div class="tabs">
                <button class="tab active" onclick="switchTab(event, 'download')">下载视频</button>
                <button class="tab" onclick="switchTab(event, 'status')">任务状态</button>
                <button class="tab" onclick="switchTab(event, 'history')">下载历史</button>
                <button class="tab" onclick="switchTab(event, 'settings')">设置</button>
            </div>

            <div id="download-tab" class="tab-content active">
                <div class="info-box">
                    <p>📁 当前下载目录: <strong id="current-work-dir">~/Downloads/BBDown-Web</strong></p>
                </div>
                
                <form id="download-form" onsubmit="return false;">
                    <div class="input-group">
                        <label>视频地址或ID (支持av/bv/ep/ss):</label>
                        <input type="text" id="url" name="url" 
                               placeholder="支持直接粘贴分享文本，如：【标题】 https://b23.tv/xxx 或 BV1qt4y1X7TW" required>
                        <div class="help-text">
                            支持格式：BV号、av号、完整链接、短链接、分享文本等
                        </div>
                    </div>

                    <div class="input-group">
                        <label>Cookie (用于下载会员视频，可选):</label>
                        <textarea id="cookie" name="cookie" placeholder="SESSDATA=xxxxx; 或完整cookie字符串"></textarea>
                    </div>

                    <div class="grid-2">
                        <div class="input-group">
                            <label>画质优先级:</label>
                            <select id="quality" name="quality">
                                <option value="">默认</option>
                                <option value="8K 超高清">8K 超高清</option>
                                <option value="杜比视界">杜比视界</option>
                                <option value="HDR 真彩">HDR 真彩</option>
                                <option value="4K 超清">4K 超清</option>
                                <option value="1080P 高码率">1080P 高码率</option>
                                <option value="1080P 高清">1080P 高清</option>
                                <option value="720P 高清">720P 高清</option>
                            </select>
                        </div>

                        <div class="input-group">
                            <label>视频编码:</label>
                            <select id="encoding" name="encoding">
                                <option value="">默认</option>
                                <option value="hevc">HEVC (H.265)</option>
                                <option value="av1">AV1</option>
                                <option value="avc">AVC (H.264)</option>
                                <option value="hevc,av1,avc">HEVC优先</option>
                                <option value="av1,hevc,avc">AV1优先</option>
                            </select>
                        </div>
                    </div>

                    <div class="checkbox-group">
                        <label><input type="checkbox" name="download_danmaku"> 下载弹幕</label>
                        <label><input type="checkbox" name="download_subtitle"> 下载字幕</label>
                        <label><input type="checkbox" name="download_cover"> 下载封面</label>
                        <label><input type="checkbox" name="video_only"> 仅下载视频</label>
                        <label><input type="checkbox" name="audio_only"> 仅下载音频</label>
                        <label><input type="checkbox" name="use_aria2"> 使用Aria2加速</label>
                    </div>

                    <span class="toggle-advanced" onclick="toggleAdvanced()">▼ 高级选项</span>
                    
                    <div class="advanced-options" id="advanced-options">
                        <div class="grid-2">
                            <div class="input-group">
                                <label>选择分P:</label>
                                <input type="text" id="select_page" name="select_page" placeholder="ALL">
                                <div class="help-text">
                                    选择指定分P或分P范围：<br>
                                    <code>8</code> - 下载第8P | 
                                    <code>1,2</code> - 下载第1P和第2P<br>
                                    <code>3-5</code> - 下载第3到5P | 
                                    <code>ALL</code> - 下载所有分P<br>
                                    <code>LAST</code> - 下载最后一P | 
                                    <code>3,5,LATEST</code> - 下载第3P、第5P和最新一P<br>
                                    默认值：<code>ALL</code>
                                </div>
                            </div>
                            
                            <div class="input-group">
                                <label>解析模式:</label>
                                <select id="api_mode" name="api_mode">
                                    <option value="">默认(WEB)</option>
                                    <option value="tv">TV端</option>
                                    <option value="app">APP端</option>
                                    <option value="intl">国际版</option>
                                </select>
                            </div>
                        </div>

                        <div class="grid-2">
                            <div class="input-group">
                                <label>分P下载间隔 (秒):</label>
                                <input type="number" id="delay_per_page" name="delay_per_page" min="0" max="300" placeholder="0">
                                <div class="help-text">设置下载合集分P之间的间隔时间，默认无间隔</div>
                            </div>
                            
                            <div class="input-group">
                                <label>自定义下载目录:</label>
                                <input type="text" id="work_dir" name="work_dir" placeholder="~/Downloads/BBDown-Web">
                                <div class="help-text">留空使用默认目录</div>
                            </div>
                        </div>

                        <div class="input-group">
                            <label>输出文件名模板:</label>
                            <input type="text" id="file_pattern" name="file_pattern" 
                                   placeholder="<videoTitle>">
                            <div class="help-text">
                                可用变量：<br>
                                <code>&lt;videoTitle&gt;</code> 视频主标题 | 
                                <code>&lt;pageNumber&gt;</code> 分P序号 | 
                                <code>&lt;pageNumberWithZero&gt;</code> 分P序号(补零) | 
                                <code>&lt;pageTitle&gt;</code> 分P标题<br>
                                <code>&lt;bvid&gt;</code> BV号 | 
                                <code>&lt;aid&gt;</code> av号 | 
                                <code>&lt;cid&gt;</code> cid | 
                                <code>&lt;dfn&gt;</code> 清晰度 | 
                                <code>&lt;res&gt;</code> 分辨率 | 
                                <code>&lt;fps&gt;</code> 帧率<br>
                                <code>&lt;videoCodecs&gt;</code> 视频编码 | 
                                <code>&lt;videoBandwidth&gt;</code> 视频码率 | 
                                <code>&lt;audioCodecs&gt;</code> 音频编码 | 
                                <code>&lt;audioBandwidth&gt;</code> 音频码率<br>
                                <code>&lt;ownerName&gt;</code> 上传者名称 | 
                                <code>&lt;ownerMid&gt;</code> 上传者mid | 
                                <code>&lt;publishDate&gt;</code> 发布时间 | 
                                <code>&lt;videoDate&gt;</code> 视频时间<br>
                                <code>&lt;apiType&gt;</code> API类型(TV/APP/INTL/WEB)<br>
                                <strong>默认值：</strong> <code>&lt;videoTitle&gt;</code><br>
                                <strong>示例：</strong> <code>&lt;videoTitle&gt;/[P&lt;pageNumberWithZero&gt;]&lt;pageTitle&gt;</code>
                            </div>
                        </div>

                        <div class="checkbox-group">
                            <label><input type="checkbox" name="skip_mux"> 跳过混流</label>
                            <label><input type="checkbox" name="force_http"> 强制HTTP</label>
                            <label><input type="checkbox" name="show_all"> 显示所有分P</label>
                            <label><input type="checkbox" name="use_mp4box"> 使用MP4Box混流</label>
                        </div>
                    </div>

                    <div class="button-group">
                        <button type="button" onclick="submitDownload()">开始下载</button>
                        <button type="button" class="secondary-btn" onclick="parseOnly()">仅解析信息</button>
                        <button type="button" class="info-btn" onclick="openDownloadFolder()">打开下载目录</button>
                        <button type="button" class="danger-btn" onclick="clearForm()">清空表单</button>
                    </div>
                </form>
            </div>

            <div id="status-tab" class="tab-content">
                <div id="status-list">
                    <p style="text-align: center; color: #718096;">暂无下载任务</p>
                </div>
            </div>

            <div id="history-tab" class="tab-content">
                <div class="button-group" style="margin-bottom: 20px;">
                    <button type="button" class="danger-btn" onclick="clearHistory()">清空历史</button>
                    <button type="button" class="info-btn" onclick="openDownloadFolder()">打开下载目录</button>
                </div>
                <div id="history-list">
                    <p style="text-align: center; color: #718096;">暂无下载历史</p>
                </div>
            </div>

            <div id="settings-tab" class="tab-content">
                <div class="settings-section">
                    <h3>基础设置</h3>
                    <div class="input-group">
                        <label>BBDown 路径:</label>
                        <input type="text" id="bbdown_path" value="~/.dotnet/tools/BBDown">
                        <small style="color: #718096;">默认路径: ~/.dotnet/tools/BBDown</small>
                    </div>
                    
                    <div class="input-group">
                        <label>默认下载目录:</label>
                        <input type="text" id="default_dir" value="~/Downloads/BBDown-Web">
                        <small style="color: #718096;">所有视频将下载到此目录</small>
                    </div>
                </div>

                <div class="settings-section">
                    <h3>工具路径设置</h3>
                    <div class="input-group">
                        <label>FFmpeg 路径 (可选):</label>
                        <input type="text" id="ffmpeg_path" placeholder="/usr/local/bin/ffmpeg">
                        <small style="color: #718096;">用于视频音频混流，留空使用系统默认</small>
                    </div>

                    <div class="input-group">
                        <label>MP4Box 路径 (可选):</label>
                        <input type="text" id="mp4box_path" placeholder="/usr/local/bin/mp4box">
                        <small style="color: #718096;">使用MP4Box替代FFmpeg进行混流</small>
                    </div>

                    <div class="input-group">
                        <label>Aria2c 路径 (可选):</label>
                        <input type="text" id="aria2c_path" placeholder="/usr/local/bin/aria2c">
                        <small style="color: #718096;">用于多线程加速下载</small>
                    </div>
                </div>

                <div class="settings-section">
                    <h3>高级设置</h3>
                    <div class="input-group">
                        <label>User-Agent (可选):</label>
                        <input type="text" id="user_agent" placeholder="留空使用随机User-Agent">
                        <small style="color: #718096;">自定义浏览器标识，某些情况下可以避免限制</small>
                    </div>

                    <div class="input-group">
                        <label>UPOS Host (可选):</label>
                        <input type="text" id="upos_host" placeholder="例如: ks3u.cos.accelerate.myqcloud.com">
                        <small style="color: #718096;">自定义下载服务器，可提升下载速度</small>
                    </div>

                    <div class="checkbox-group">
                        <label><input type="checkbox" id="enable_debug"> 启用调试日志（显示详细下载信息）</label>
                    </div>
                </div>

                <div class="button-group">
                    <button onclick="saveSettings()">保存设置</button>
                    <button type="button" class="info-btn" onclick="checkBBDown()" style="margin-left: 10px;">检查BBDown</button>
                    <button type="button" class="secondary-btn" onclick="testTools()" style="margin-left: 10px;">测试工具路径</button>
                </div>
            </div>
        </div>

        <div class="card" id="log-card" style="display: none;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3>下载日志</h3>
                <button type="button" class="info-btn" onclick="clearLog()" style="padding: 6px 12px; font-size: 14px;">清空日志</button>
            </div>
            <div class="log-output" id="log-output"></div>
        </div>
    </div>

    <div class="footer">
        BBDown Web GUI v""" + APP_VERSION + """ | 
        基于 <a href="https://github.com/nilaoda/BBDown" target="_blank">BBDown</a> | 
        <a href="https://github.com" target="_blank">GitHub</a>
    </div>

    <!-- 通知容器 -->
    <div class="notification-container" id="notification-container"></div>

    <!-- 确认对话框 -->
    <div class="modal-overlay" id="modal-overlay">
        <div class="modal">
            <div class="modal-title" id="modal-title">确认</div>
            <div class="modal-message" id="modal-message">您确定要执行此操作吗？</div>
            <div class="modal-buttons">
                <button class="modal-button secondary" onclick="closeModal(false)">取消</button>
                <button class="modal-button primary" id="modal-confirm">确定</button>
            </div>
        </div>
    </div>

    <script>
        let currentTaskId = null;
        let logUpdateInterval = null;
        let currentWorkDir = '~/Downloads/BBDown-Web';
        let activeNewTaskId = null;  // 记录当前活动的新任务ID
        let userIsScrolling = false;  // 标记用户是否正在滚动
        let autoScrollEnabled = true;  // 是否启用自动滚动
        let justSwitchedTask = false;  // 标记是否刚切换任务

        // 监听日志输出区的滚动事件
        document.addEventListener('DOMContentLoaded', function() {
            const logOutput = document.getElementById('log-output');
            
            // 监听滚动事件
            logOutput.addEventListener('scroll', function() {
                // 如果刚切换任务，不处理这个滚动事件
                if (justSwitchedTask) {
                    justSwitchedTask = false;
                    return;
                }
                
                const scrollTop = logOutput.scrollTop;
                const scrollHeight = logOutput.scrollHeight;
                const clientHeight = logOutput.clientHeight;
                
                // 如果用户滚动到底部附近（误差10px），启用自动滚动
                if (scrollHeight - scrollTop - clientHeight < 10) {
                    autoScrollEnabled = true;
                } else {
                    // 用户向上滚动，禁用自动滚动
                    autoScrollEnabled = false;
                }
            });
            
            // 鼠标进入日志区域时，暂时禁用自动滚动
            logOutput.addEventListener('mouseenter', function() {
                userIsScrolling = true;
            });
            
            // 鼠标离开日志区域后，检查是否在底部
            logOutput.addEventListener('mouseleave', function() {
                userIsScrolling = false;
                const scrollTop = logOutput.scrollTop;
                const scrollHeight = logOutput.scrollHeight;
                const clientHeight = logOutput.clientHeight;
                
                // 如果在底部附近，重新启用自动滚动
                if (scrollHeight - scrollTop - clientHeight < 10) {
                    autoScrollEnabled = true;
                }
            });
        });

        // 通知系统
        function showNotification(message, type = 'info', title = '') {
            const container = document.getElementById('notification-container');
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            
            const icons = {
                success: '✅',
                error: '❌',
                info: 'ℹ️',
                warning: '⚠️'
            };
            
            const titles = {
                success: '成功',
                error: '错误',
                info: '提示',
                warning: '警告'
            };
            
            notification.innerHTML = `
                <div class="notification-icon">${icons[type]}</div>
                <div class="notification-content">
                    <div class="notification-title">${title || titles[type]}</div>
                    <div class="notification-message">${message}</div>
                </div>
                <button class="notification-close" onclick="removeNotification(this.parentElement)">×</button>
            `;
            
            container.appendChild(notification);
            
            // 自动移除通知
            setTimeout(() => {
                removeNotification(notification);
            }, 5000);
        }
        
        function removeNotification(notification) {
            if (!notification || !notification.parentElement) return;
            notification.classList.add('removing');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }

        // 自定义确认对话框
        function showConfirm(message, title = '确认', callback = null) {
            const overlay = document.getElementById('modal-overlay');
            const modalTitle = document.getElementById('modal-title');
            const modalMessage = document.getElementById('modal-message');
            const confirmBtn = document.getElementById('modal-confirm');
            
            modalTitle.textContent = title;
            modalMessage.textContent = message;
            
            overlay.classList.add('active');
            
            // 移除旧的事件监听器
            const newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
            
            newConfirmBtn.onclick = () => {
                closeModal(true);
                if (callback) callback();
            };
        }
        
        function closeModal(result) {
            const overlay = document.getElementById('modal-overlay');
            overlay.classList.remove('active');
        }

        function switchTab(event, tabName) {
            // 移除所有活动状态
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            // 添加活动状态
            event.target.classList.add('active');
            document.getElementById(tabName + '-tab').classList.add('active');
            
            // 根据标签页更新数据
            if (tabName === 'status') {
                updateStatus();
            } else if (tabName === 'history') {
                updateHistory();
            } else if (tabName === 'settings') {
                loadSettings();
            }
        }

        function toggleAdvanced() {
            const advanced = document.getElementById('advanced-options');
            const toggle = document.querySelector('.toggle-advanced');
            if (advanced.style.display === 'none' || !advanced.style.display) {
                advanced.style.display = 'block';
                toggle.textContent = '▲ 高级选项';
            } else {
                advanced.style.display = 'none';
                toggle.textContent = '▼ 高级选项';
            }
        }

        function formatLogHtml(text) {
            // 为不同日志级别添加HTML颜色标记
            return text
                .replace(/\[(\d{2}:\d{2}:\d{2})\]/g, '<span class="log-timestamp">[$1]</span>')
                .replace(/\[INFO\]/g, '<span class="log-info">[INFO]</span>')
                .replace(/\[SUCCESS\]/g, '<span class="log-success">[SUCCESS]</span>')
                .replace(/\[ERROR\]/g, '<span class="log-error">[ERROR]</span>')
                .replace(/\[WARN\]/g, '<span class="log-warning">[WARN]</span>')
                .replace(/\[DEBUG\]/g, '<span class="log-debug">[DEBUG]</span>')
                .replace(/\[PROGRESS\]/g, '<span class="log-progress">[PROGRESS]</span>')
                .replace(/(\d+)%/g, '<span class="log-progress">$1%</span>')
                .replace(/(={5,})/g, '<span class="log-separator">$1</span>')
                .replace(/(✅)/g, '<span class="log-success">$1</span>')
                .replace(/(❌)/g, '<span class="log-error">$1</span>');
        }

        function extractUrl(input) {
            // 尝试从输入中提取URL
            input = input.trim();
            
            // 匹配各种B站链接格式
            const urlPatterns = [
                /https?:\/\/[^\s]+/,  // 任何http/https链接
                /b23\.tv\/[^\s]+/,    // 短链接
                /BV[a-zA-Z0-9]+/,     // BV号
                /av\d+/i,             // av号
                /ep\d+/i,             // 番剧
                /ss\d+/i              // 番剧season
            ];
            
            for (const pattern of urlPatterns) {
                const match = input.match(pattern);
                if (match) {
                    let url = match[0];
                    // 如果是短链接但没有协议，添加https
                    if (url.startsWith('b23.tv')) {
                        url = 'https://' + url;
                    }
                    return url;
                }
            }
            
            // 如果没有匹配到，返回原始输入（可能本身就是有效的）
            return input;
        }

        async function submitDownload() {
            const form = document.getElementById('download-form');
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            // 验证并提取URL
            if (!data.url || data.url.trim() === '') {
                showNotification('请输入视频地址', 'warning');
                return;
            }
            
            // 从输入中提取URL
            data.url = extractUrl(data.url);
            
            // 处理复选框
            const checkboxes = ['download_danmaku', 'download_subtitle', 'download_cover', 
                               'video_only', 'audio_only', 'use_aria2', 
                               'skip_mux', 'force_http', 'show_all', 'use_mp4box'];
            checkboxes.forEach(name => {
                data[name] = document.querySelector(`input[name="${name}"]`).checked;
            });
            
            // 如果没有自定义目录，使用默认目录
            if (!data.work_dir || data.work_dir.trim() === '') {
                data.work_dir = currentWorkDir;
            }
            
            // 添加设置中的配置
            const settings = await getSettings();
            if (settings) {
                data.debug = settings.enable_debug;
                data.user_agent = settings.user_agent;
                data.ffmpeg_path = settings.ffmpeg_path;
                data.mp4box_path = settings.mp4box_path;
                data.upos_host = settings.upos_host;
            }
            
            try {
                const response = await fetch('/api/download', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                if (result.success) {
                    currentTaskId = result.task_id;
                    activeNewTaskId = result.task_id;  // 记录新任务ID
                    autoScrollEnabled = true;  // 新任务默认启用自动滚动
                    showLog();
                    startLogUpdate(currentTaskId, true);  // 新任务，自动滚动
                    // 切换到状态标签页
                    document.querySelector('.tab:nth-child(2)').click();
                    showNotification('下载任务已添加到队列', 'success');
                } else {
                    showNotification(result.message, 'error');
                }
            } catch (error) {
                showNotification('请求失败: ' + error, 'error');
            }
        }

        async function parseOnly() {
            let url = document.getElementById('url').value;
            if (!url) {
                showNotification('请输入视频地址', 'warning');
                return;
            }
            
            // 从输入中提取URL
            url = extractUrl(url);
            
            try {
                const response = await fetch('/api/parse', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        url: url, 
                        cookie: document.getElementById('cookie').value
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    // 在日志窗口显示解析信息
                    document.getElementById('log-card').style.display = 'block';
                    const logOutput = document.getElementById('log-output');
                    // 使用innerHTML显示带颜色的日志
                    logOutput.innerHTML = formatLogHtml(data.info);
                    showNotification('解析成功', 'success');
                } else {
                    showNotification('解析失败: ' + data.message, 'error');
                }
            } catch (error) {
                showNotification('请求失败: ' + error, 'error');
            }
        }

        function clearForm() {
            showConfirm('确定要清空表单吗？', '清空表单', () => {
                document.getElementById('download-form').reset();
                showNotification('表单已清空', 'info');
            });
        }

        function clearLog() {
            document.getElementById('log-output').innerHTML = '';
            showNotification('日志已清空', 'info');
        }

        function showLog() {
            document.getElementById('log-card').style.display = 'block';
        }

        function startLogUpdate(taskId, isNewTask = false) {
            if (logUpdateInterval) {
                clearInterval(logUpdateInterval);
            }
            
            let notificationShown = false;  // 防止重复通知
            let lastStatus = null;  // 记录上一次的状态
            let firstLoad = true;  // 标记是否首次加载
            
            logUpdateInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/api/task/${taskId}/log`);
                    const data = await response.json();
                    
                    if (data.log) {
                        const logOutput = document.getElementById('log-output');
                        // 使用innerHTML显示带颜色的日志
                        logOutput.innerHTML = formatLogHtml(data.log);
                        
                        // 首次加载时，如果不是新任务，滚动到顶部
                        if (firstLoad && !isNewTask) {
                            justSwitchedTask = true;  // 标记刚切换任务
                            logOutput.scrollTop = 0;  // 滚动到顶部
                            autoScrollEnabled = false;  // 默认不自动滚动
                            firstLoad = false;
                        } else if (firstLoad && isNewTask) {
                            // 新任务首次加载，滚动到底部
                            logOutput.scrollTop = logOutput.scrollHeight;
                            firstLoad = false;
                        } else if (autoScrollEnabled && !userIsScrolling) {
                            // 只有在自动滚动启用且用户没有正在滚动时才自动滚动到底部
                            logOutput.scrollTop = logOutput.scrollHeight;
                        }
                    }
                    
                    // 只有当前任务是新提交的任务，且状态发生变化时才显示通知
                    if (taskId === activeNewTaskId && !notificationShown && lastStatus !== data.status) {
                        if (data.status === 'completed' || data.status === 'failed') {
                            clearInterval(logUpdateInterval);
                            updateStatus();
                            notificationShown = true;
                            activeNewTaskId = null;  // 清除活动任务ID
                            
                            if (data.status === 'completed') {
                                showNotification('下载任务已完成！', 'success', '下载完成');
                            } else if (data.status === 'failed') {
                                showNotification('下载任务失败，请查看日志了解详情', 'error', '下载失败');
                            }
                        }
                    }
                    
                    lastStatus = data.status;
                } catch (error) {
                    console.error('获取日志失败:', error);
                }
            }, 1000);
        }

        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                const statusList = document.getElementById('status-list');
                
                if (data.tasks && data.tasks.length > 0) {
                    statusList.innerHTML = data.tasks.map(task => `
                        <div class="status-item status-${task.status}">
                            <div style="flex: 1;">
                                <strong>${task.title || task.url}</strong>
                                <br><small>状态: ${task.status} | 开始时间: ${task.start_time}</small>
                                ${task.progress ? `<div class="progress-bar"><div class="progress-fill" style="width: ${task.progress}%"></div></div>` : ''}
                            </div>
                            <button onclick="viewTaskLog('${task.id}')">查看日志</button>
                        </div>
                    `).join('');
                } else {
                    statusList.innerHTML = '<p style="text-align: center; color: #718096;">暂无下载任务</p>';
                }
            } catch (error) {
                console.error('更新状态失败:', error);
            }
        }

        async function updateHistory() {
            try {
                const response = await fetch('/api/history');
                const data = await response.json();
                const historyList = document.getElementById('history-list');
                
                if (data.history && data.history.length > 0) {
                    historyList.innerHTML = data.history.map(item => `
                        <div class="status-item">
                            <div>
                                <strong>${item.title}</strong>
                                <br><small>下载时间: ${item.time} | 状态: ${item.status}</small>
                            </div>
                        </div>
                    `).join('');
                } else {
                    historyList.innerHTML = '<p style="text-align: center; color: #718096;">暂无下载历史</p>';
                }
            } catch (error) {
                console.error('更新历史失败:', error);
            }
        }

        function viewTaskLog(taskId) {
            // 切换任务时，重置自动滚动为false（查看历史任务默认不自动滚动）
            if (currentTaskId !== taskId) {
                autoScrollEnabled = false;  // 查看不同任务时默认不自动滚动
            }
            currentTaskId = taskId;
            showLog();
            // 查看历史日志时，传入false表示不是新任务
            startLogUpdate(taskId, false);
        }

        async function getSettings() {
            try {
                const response = await fetch('/api/settings');
                const data = await response.json();
                if (data.success) {
                    return data.settings;
                }
            } catch (error) {
                console.error('获取设置失败:', error);
            }
            return null;
        }

        async function saveSettings() {
            const settings = {
                bbdown_path: document.getElementById('bbdown_path').value,
                default_dir: document.getElementById('default_dir').value,
                aria2c_path: document.getElementById('aria2c_path').value,
                ffmpeg_path: document.getElementById('ffmpeg_path').value,
                mp4box_path: document.getElementById('mp4box_path').value,
                user_agent: document.getElementById('user_agent').value,
                upos_host: document.getElementById('upos_host').value,
                enable_debug: document.getElementById('enable_debug').checked
            };
            
            try {
                const response = await fetch('/api/settings', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(settings)
                });
                
                const data = await response.json();
                if (data.success) {
                    currentWorkDir = settings.default_dir;
                    document.getElementById('current-work-dir').textContent = currentWorkDir;
                    showNotification('设置已保存', 'success');
                } else {
                    showNotification('保存失败: ' + data.message, 'error');
                }
            } catch (error) {
                showNotification('保存设置失败: ' + error, 'error');
            }
        }

        async function loadSettings() {
            try {
                const response = await fetch('/api/settings');
                const data = await response.json();
                if (data.success) {
                    document.getElementById('bbdown_path').value = data.settings.bbdown_path || '~/.dotnet/tools/BBDown';
                    document.getElementById('default_dir').value = data.settings.default_dir || '~/Downloads/BBDown-Web';
                    document.getElementById('aria2c_path').value = data.settings.aria2c_path || '';
                    document.getElementById('ffmpeg_path').value = data.settings.ffmpeg_path || '';
                    document.getElementById('mp4box_path').value = data.settings.mp4box_path || '';
                    document.getElementById('user_agent').value = data.settings.user_agent || '';
                    document.getElementById('upos_host').value = data.settings.upos_host || '';
                    document.getElementById('enable_debug').checked = data.settings.enable_debug || false;
                    currentWorkDir = data.settings.default_dir || '~/Downloads/BBDown-Web';
                    document.getElementById('current-work-dir').textContent = currentWorkDir;
                }
            } catch (error) {
                console.error('加载设置失败:', error);
            }
        }

        async function clearHistory() {
            showConfirm('确定要清空所有下载历史吗？', '清空历史', async () => {
                try {
                    const response = await fetch('/api/history/clear', {
                        method: 'POST'
                    });
                    const data = await response.json();
                    if (data.success) {
                        updateHistory();
                        showNotification('历史已清空', 'success');
                    }
                } catch (error) {
                    showNotification('清空历史失败: ' + error, 'error');
                }
            });
        }

        async function openDownloadFolder() {
            try {
                const response = await fetch('/api/open-folder', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({path: currentWorkDir})
                });
                const data = await response.json();
                if (!data.success) {
                    showNotification('打开文件夹失败: ' + data.message, 'error');
                }
            } catch (error) {
                showNotification('打开文件夹失败: ' + error, 'error');
            }
        }

        async function checkBBDown() {
            try {
                const response = await fetch('/api/check-bbdown');
                const data = await response.json();
                if (data.installed) {
                    showNotification(
                        `版本: ${data.version}<br>路径: ${data.path}`,
                        'success',
                        'BBDown 已安装'
                    );
                } else {
                    showNotification('BBDown 未安装或路径不正确', 'warning');
                }
            } catch (error) {
                showNotification('检查失败: ' + error, 'error');
            }
        }

        async function testTools() {
            try {
                const response = await fetch('/api/test-tools');
                const data = await response.json();
                let message = '';
                for (const [tool, result] of Object.entries(data.tools)) {
                    message += `${tool}: ${result.installed ? '✅ 已安装' : '❌ 未找到'}`;
                    if (result.version) {
                        message += ` (${result.version})`;
                    }
                    message += '<br>';
                }
                showNotification(message, 'info', '工具检测结果');
            } catch (error) {
                showNotification('测试失败: ' + error, 'error');
            }
        }

        // 页面加载时更新状态和加载设置
        window.addEventListener('load', () => {
            updateStatus();
            loadSettings();
        });
        
        // 定期更新状态
        setInterval(() => {
            const statusTab = document.getElementById('status-tab');
            if (statusTab.classList.contains('active')) {
                updateStatus();
            }
        }, 5000);
    </script>
</body>
</html>
"""

# 后端代码保持不变...
def extract_url_from_text(text):
    """从文本中提取B站URL"""
    text = text.strip()
    
    # 定义匹配模式
    patterns = [
        r'https?://[^\s]+',  # 完整URL
        r'b23\.tv/[^\s]+',   # 短链接
        r'BV[a-zA-Z0-9]+',   # BV号
        r'av\d+',            # av号
        r'ep\d+',            # 番剧ep
        r'ss\d+',            # 番剧ss
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            url = match.group(0)
            # 如果是短链接但没有协议，添加https
            if url.startswith('b23.tv'):
                url = 'https://' + url
            return url
    
    # 如果没有匹配到，返回原始文本
    return text

class DownloadTask:
    def __init__(self, task_id, url, options):
        self.id = task_id
        self.url = url
        self.options = options
        self.status = "pending"
        self.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log = ""
        self.title = url
        self.progress = 0

# 配置存储
app_settings = {
    'bbdown_path': '~/.dotnet/tools/BBDown',
    'default_dir': '~/Downloads/BBDown-Web',
    'aria2c_path': '',
    'ffmpeg_path': '',
    'mp4box_path': '',
    'user_agent': '',
    'upos_host': '',
    'enable_debug': False
}

def format_log_line(line):
    """格式化日志行，添加时间戳和级别标记，确保有换行"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # 如果行为空，只返回换行
    if not line or line.strip() == '':
        return '\n'
    
    # 识别不同类型的日志行
    if any(keyword in line for keyword in ['错误', 'ERROR', 'Failed', 'failed']):
        return f"[{timestamp}] [ERROR] {line}\n"
    elif any(keyword in line for keyword in ['警告', 'WARNING', 'Warning']):
        return f"[{timestamp}] [WARN] {line}\n"
    elif any(keyword in line for keyword in ['成功', 'SUCCESS', 'Completed', '完成', '✅']):
        return f"[{timestamp}] [SUCCESS] {line}\n"
    elif any(keyword in line for keyword in ['调试', 'DEBUG', 'Debug']):
        return f"[{timestamp}] [DEBUG] {line}\n"
    elif '%' in line:  # 进度信息
        return f"[{timestamp}] [PROGRESS] {line}\n"
    else:
        return f"[{timestamp}] [INFO] {line}\n"

def download_worker():
    """后台下载线程"""
    while True:
        try:
            task = download_queue.get(timeout=1)
            if task is None:
                break
                
            task.status = "downloading"
            download_status[task.id] = task
            
            # 构建BBDown命令
            cmd = build_bbdown_command(task.url, task.options)
            
            # 格式化命令显示
            cmd_display = ' '.join(cmd[:3]) + '...' if len(cmd) > 3 else ' '.join(cmd)
            
            # 添加初始日志，每行都确保有换行
            task.log = format_log_line("========== 开始新的下载任务 ==========")
            task.log += format_log_line(f"视频URL: {task.url}")
            task.log += format_log_line(f"下载目录: {task.options.get('work_dir', DEFAULT_WORK_DIR)}")
            task.log += format_log_line(f"执行命令: {cmd_display}")
            task.log += format_log_line("========================================")
            task.log += '\n'  # 额外的空行分隔
            
            # 执行下载
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 实时更新日志
            for line in iter(process.stdout.readline, ''):
                if line:
                    # 去除原始换行，由format_log_line添加
                    formatted_line = format_log_line(line.rstrip('\n\r'))
                    task.log += formatted_line
                    
                    # 尝试解析进度
                    progress_match = re.search(r'(\d+)%', line)
                    if progress_match:
                        task.progress = int(progress_match.group(1))
                    
                    # 尝试提取视频标题
                    if '视频标题:' in line or 'Title:' in line:
                        title_match = re.search(r'[视频标题|Title]:\s*(.+)', line)
                        if title_match:
                            task.title = title_match.group(1).strip()
            
            process.wait()
            
            # 结束日志
            task.log += '\n'  # 空行分隔
            task.log += format_log_line("========================================")
            if process.returncode == 0:
                task.status = "completed"
                task.progress = 100
                task.log += format_log_line("✅ 下载任务完成！")
            else:
                task.status = "failed"
                task.log += format_log_line(f"❌ 下载失败，返回码: {process.returncode}")
            task.log += format_log_line("========== 任务结束 ==========")
            task.log += '\n'
                
            # 保存到历史
            download_history.append({
                'title': task.title,
                'url': task.url,
                'time': task.start_time,
                'status': task.status
            })
            
        except queue.Empty:
            continue
        except Exception as e:
            if 'task' in locals() and task:
                task.status = "failed"
                task.log += format_log_line(f"❌ 系统错误: {str(e)}")

def build_bbdown_command(url, options):
    """构建BBDown命令行参数"""
    bbdown_path = os.path.expanduser(options.get('bbdown_path', app_settings['bbdown_path']))
    
    # 如果BBDown不存在，尝试直接使用BBDown命令
    if not os.path.exists(bbdown_path):
        bbdown_path = 'BBDown'
    
    cmd = [bbdown_path, url]
    
    # Cookie
    if options.get('cookie'):
        cookie = options['cookie'].strip()
        if cookie:
            cmd.extend(['-c', cookie])
    
    # 画质
    if options.get('quality'):
        cmd.extend(['-q', options['quality']])
    
    # 编码
    if options.get('encoding'):
        cmd.extend(['-e', options['encoding']])
    
    # 分P选择
    if options.get('select_page'):
        cmd.extend(['-p', options['select_page']])
    
    # API模式
    if options.get('api_mode'):
        if options['api_mode'] == 'tv':
            cmd.append('--use-tv-api')
        elif options['api_mode'] == 'app':
            cmd.append('--use-app-api')
        elif options['api_mode'] == 'intl':
            cmd.append('--use-intl-api')
    
    # 分P下载间隔
    if options.get('delay_per_page'):
        try:
            delay = int(options['delay_per_page'])
            if delay > 0:
                cmd.extend(['--delay-per-page', str(delay)])
        except:
            pass
    
    # 布尔选项
    if options.get('download_danmaku'):
        cmd.append('--download-danmaku')
    if options.get('video_only'):
        cmd.append('--video-only')
    if options.get('audio_only'):
        cmd.append('--audio-only')
    if options.get('use_aria2'):
        cmd.append('--use-aria2c')
        if options.get('aria2c_path'):
            cmd.extend(['--aria2c-path', os.path.expanduser(options['aria2c_path'])])
    if options.get('skip_mux'):
        cmd.append('--skip-mux')
    if options.get('force_http'):
        cmd.append('--force-http')
    if options.get('show_all'):
        cmd.append('--show-all')
    if options.get('use_mp4box'):
        cmd.append('--use-mp4box')
        if options.get('mp4box_path'):
            cmd.extend(['--mp4box-path', os.path.expanduser(options['mp4box_path'])])
    if not options.get('download_subtitle', True):
        cmd.append('--skip-subtitle')
    if not options.get('download_cover', True):
        cmd.append('--skip-cover')
    
    # 高级选项
    if options.get('debug'):
        cmd.append('--debug')
    
    if options.get('user_agent'):
        cmd.extend(['-ua', options['user_agent']])
    
    if options.get('ffmpeg_path'):
        cmd.extend(['--ffmpeg-path', os.path.expanduser(options['ffmpeg_path'])])
    
    if options.get('upos_host'):
        cmd.extend(['--upos-host', options['upos_host']])
    
    # 文件名模板
    if options.get('file_pattern'):
        cmd.extend(['-F', options['file_pattern']])
    
    # 工作目录 - 使用默认目录或用户指定的目录
    work_dir = options.get('work_dir', DEFAULT_WORK_DIR)
    if not work_dir:
        work_dir = DEFAULT_WORK_DIR
    work_dir = os.path.expanduser(work_dir)
    os.makedirs(work_dir, exist_ok=True)
    cmd.extend(['--work-dir', work_dir])
    
    return cmd

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/download", methods=["POST"])
def api_download():
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'message': '请输入视频地址'})
        
        # 从文本中提取URL
        url = extract_url_from_text(url)
        
        # 创建下载任务
        task_id = f"task_{int(time.time() * 1000)}"
        
        # 合并全局设置
        for key in ['bbdown_path', 'ffmpeg_path', 'mp4box_path', 'user_agent', 'upos_host', 'debug']:
            if key not in data or not data[key]:
                data[key] = app_settings.get(key, '')
        
        # 设置默认下载目录
        if not data.get('work_dir') or data['work_dir'].strip() == '':
            data['work_dir'] = app_settings['default_dir']
        
        task = DownloadTask(task_id, url, data)
        
        # 添加到队列
        download_queue.put(task)
        download_status[task_id] = task
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '下载任务已添加到队列'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route("/api/parse", methods=["POST"])
def api_parse():
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'message': '请输入视频地址'})
        
        # 从文本中提取URL
        url = extract_url_from_text(url)
        
        bbdown_path = os.path.expanduser(app_settings['bbdown_path'])
        if not os.path.exists(bbdown_path):
            bbdown_path = 'BBDown'
            
        cmd = [bbdown_path, url, '--only-show-info']
        
        if data.get('cookie'):
            cookie = data['cookie'].strip()
            if cookie:
                cmd.extend(['-c', cookie])
        
        # 添加调试选项
        if app_settings.get('enable_debug'):
            cmd.append('--debug')
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            formatted_output = ""
            for line in result.stdout.split('\n'):
                if line.strip():
                    formatted_output += format_log_line(line.strip())
            return jsonify({'success': True, 'info': formatted_output})
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            return jsonify({'success': False, 'message': error_msg})
            
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': '解析超时'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route("/api/status", methods=["GET"])
def api_status():
    tasks = []
    for task_id, task in list(download_status.items())[-10:]:  # 只显示最近10个任务
        tasks.append({
            'id': task.id,
            'url': task.url,
            'title': task.title,
            'status': task.status,
            'start_time': task.start_time,
            'progress': task.progress
        })
    return jsonify({'tasks': tasks[::-1]})  # 倒序显示，最新的在前

@app.route("/api/task/<task_id>/log", methods=["GET"])
def api_task_log(task_id):
    task = download_status.get(task_id)
    if task:
        return jsonify({
            'log': task.log[-20000:],  # 限制日志长度
            'status': task.status,
            'progress': task.progress
        })
    return jsonify({'log': '', 'status': 'not_found'})

@app.route("/api/history", methods=["GET"])
def api_history():
    # 返回最近50条，倒序
    return jsonify({'history': download_history[-50:][::-1]})

@app.route("/api/history/clear", methods=["POST"])
def api_clear_history():
    global download_history
    download_history = []
    return jsonify({'success': True, 'message': '历史已清空'})

@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    return jsonify({'success': True, 'settings': app_settings})

@app.route("/api/settings", methods=["POST"])
def api_save_settings():
    try:
        global app_settings
        settings = request.json
        
        # 更新设置
        for key in ['bbdown_path', 'default_dir', 'aria2c_path', 'ffmpeg_path', 
                   'mp4box_path', 'user_agent', 'upos_host', 'enable_debug']:
            if key in settings:
                app_settings[key] = settings[key]
        
        # 创建目录如果不存在
        if 'default_dir' in settings:
            dir_path = os.path.expanduser(settings['default_dir'])
            os.makedirs(dir_path, exist_ok=True)
        
        return jsonify({'success': True, 'message': '设置已保存'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route("/api/open-folder", methods=["POST"])
def api_open_folder():
    try:
        data = request.json
        path = os.path.expanduser(data.get('path', DEFAULT_WORK_DIR))
        
        # 确保目录存在
        os.makedirs(path, exist_ok=True)
        
        # 根据操作系统打开文件夹
        import platform
        system = platform.system()
        
        if system == 'Darwin':  # macOS
            subprocess.run(['open', path])
        elif system == 'Windows':
            subprocess.run(['explorer', path])
        else:  # Linux
            subprocess.run(['xdg-open', path])
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route("/api/check-bbdown", methods=["GET"])
def api_check_bbdown():
    try:
        bbdown_path = os.path.expanduser(app_settings['bbdown_path'])
        
        # 尝试多个可能的路径
        paths_to_check = [
            bbdown_path,
            'BBDown',
            '/usr/local/bin/BBDown',
            '~/.dotnet/tools/BBDown'
        ]
        
        for path in paths_to_check:
            path = os.path.expanduser(path)
            try:
                result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return jsonify({
                        'installed': True,
                        'path': path,
                        'version': result.stdout.strip()
                    })
            except:
                continue
        
        return jsonify({'installed': False, 'message': 'BBDown未找到'})
    except Exception as e:
        return jsonify({'installed': False, 'message': str(e)})

@app.route("/api/test-tools", methods=["GET"])
def api_test_tools():
    """测试各个工具是否已安装"""
    tools = {}
    
    # 测试FFmpeg
    ffmpeg_path = app_settings.get('ffmpeg_path') or 'ffmpeg'
    try:
        result = subprocess.run([ffmpeg_path, '-version'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            version_match = re.search(r'ffmpeg version ([\d.]+)', result.stdout)
            tools['FFmpeg'] = {
                'installed': True,
                'version': version_match.group(1) if version_match else 'Unknown'
            }
        else:
            tools['FFmpeg'] = {'installed': False}
    except:
        tools['FFmpeg'] = {'installed': False}
    
    # 测试MP4Box
    mp4box_path = app_settings.get('mp4box_path') or 'mp4box'
    try:
        result = subprocess.run([mp4box_path, '-version'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            tools['MP4Box'] = {'installed': True, 'version': 'Installed'}
        else:
            tools['MP4Box'] = {'installed': False}
    except:
        tools['MP4Box'] = {'installed': False}
    
    # 测试Aria2c
    aria2c_path = app_settings.get('aria2c_path') or 'aria2c'
    try:
        result = subprocess.run([aria2c_path, '--version'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            version_match = re.search(r'aria2 version ([\d.]+)', result.stdout)
            tools['Aria2c'] = {
                'installed': True,
                'version': version_match.group(1) if version_match else 'Unknown'
            }
        else:
            tools['Aria2c'] = {'installed': False}
    except:
        tools['Aria2c'] = {'installed': False}
    
    return jsonify({'success': True, 'tools': tools})

if __name__ == "__main__":
    # 创建默认下载目录
    os.makedirs(os.path.expanduser(DEFAULT_WORK_DIR), exist_ok=True)
    
    # 启动下载工作线程
    worker_thread = threading.Thread(target=download_worker, daemon=True)
    worker_thread.start()
    
    print("=" * 50)
    print(f"BBDown Web GUI v{APP_VERSION}")
    print("=" * 50)
    print("启动中...")
    print(f"默认下载目录: {DEFAULT_WORK_DIR}")
    print("请访问 http://localhost:5555")
    print("按 Ctrl+C 退出")
    print("=" * 50)
    
    # 启动Flask应用
    try:
        app.run(host="0.0.0.0", port=5555, debug=False)
    except KeyboardInterrupt:
        print("\n正在退出...")
