# -*- coding: utf-8 -*-
"""
搜索工具函数
包含HTTP请求、文本清理等通用工具
"""
import re
import time
import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://www.gequbao.net/',
}


def clean_song_title(title):
    """清理歌曲名，生成多级搜索关键词"""
    variants = []
    variants.append(title)

    cleaned = re.sub(r'（[^）]*）', '', title)
    cleaned = re.sub(r'\([^)]*\)', '', cleaned)
    cleaned = cleaned.strip()
    if cleaned and cleaned != title:
        variants.append(cleaned)

    cleaned2 = re.sub(r'\s*feat\.?\s*\S+', '', title, flags=re.IGNORECASE)
    cleaned2 = cleaned2.strip()
    if cleaned2 and cleaned2 not in variants:
        variants.append(cleaned2)

    cleaned3 = re.sub(r'\s*(with|ft\.?|feat\.?)\s*.*$', '', title, flags=re.IGNORECASE)
    cleaned3 = cleaned3.strip()
    if cleaned3 and cleaned3 not in variants and cleaned3 != title:
        variants.append(cleaned3)

    seen = set()
    result = []
    for v in variants:
        v = v.strip()
        if v and v not in seen and len(v) >= 2:
            seen.add(v)
            result.append(v)

    return result


def clean_singer_name(singer):
    """清理歌手名"""
    variants = [singer]

    first_singer = re.split(r'[,，、/\\&和]', singer)[0].strip()
    if first_singer and first_singer != singer:
        variants.append(first_singer)

    cleaned = re.sub(r'\s*feat\.\s*\S+', '', singer, flags=re.IGNORECASE).strip()
    if cleaned and cleaned not in variants:
        variants.append(cleaned)

    chinese_match = re.search(r'[\u4e00-\u9fa5]+', singer)
    if chinese_match:
        chinese_name = chinese_match.group()
        if chinese_name not in variants and len(chinese_name) >= 2:
            variants.append(chinese_name)

    seen = set()
    return [v for v in variants if v and v not in seen and not seen.add(v)]


def make_request(session, url, max_retries=3, timeout=15):
    """带重试的HTTP请求"""
    for attempt in range(max_retries):
        try:
            resp = session.get(url, timeout=timeout)
            return resp, None
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None, f"超时（重试{max_retries}次）"
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None, f"连接失败（重试{max_retries}次）"
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return None, str(e)
    return None, "未知错误"


def _normalize_text(text):
    """规范化文本用于比较：统一分隔符、空格、大小写"""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[&,，、/\\+]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
