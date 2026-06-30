# -*- coding: utf-8 -*-
"""
Flask Web 服务器 - 音乐搜索工具后端模块
提供 API 接口和静态页面服务
被 desktop.py 桌面版调用
"""
import os
from flask import Flask, send_from_directory
from routes import api_bp

app = Flask(__name__, static_folder=None)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, 'web')

app.register_blueprint(api_bp, url_prefix='/api')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    if path == '' or path is None:
        path = 'index.html'
    
    file_path = os.path.join(WEB_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(WEB_DIR, path)
    else:
        return send_from_directory(WEB_DIR, 'index.html')
