# -*- coding: utf-8 -*-
"""
桌面版入口 - 使用 PyWebView 包装 Web 应用
"""
import os
import sys
import threading
import socket

import webview


def find_free_port():
    """获取一个空闲端口"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def start_flask(port):
    """启动 Flask 服务"""
    from app import app
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


def main():
    print("🎵 夸克音乐搜索助手 - 桌面版")
    print("-" * 40)
    
    # 启动 Flask 服务
    port = find_free_port()
    server_thread = threading.Thread(target=start_flask, args=(port,), daemon=True)
    server_thread.start()
    
    print(f"服务启动中...")
    print(f"请稍候...")
    
    # 创建窗口
    window = webview.create_window(
        title='夸克音乐搜索助手',
        url=f'http://127.0.0.1:{port}',
        width=1200,
        height=800,
        resizable=True,
        js_api=None
    )
    
    # 启动应用
    webview.start(debug=False)


if __name__ == '__main__':
    main()
