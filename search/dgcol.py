# -*- coding: utf-8 -*-
"""
dgcol.com 搜索源 - 动感酷音乐
"""
import re
import urllib.parse

from bs4 import BeautifulSoup

from search.utils import make_request, _normalize_text
from search.matching import _title_match_score, _singer_match_score, _quality_penalty

DGCOL_BASE = "https://www.dgcol.com"
DGCOL_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://www.dgcol.com/',
}


def dgcol_search_all(session, title, singer=""):
    """
    在 dgcol.com 搜索歌曲，返回所有候选版本

    返回: {'candidates': [...], 'search_method': str}
    """
    candidates = []
    search_method = ""

    search_queries = []
    if singer:
        search_queries.append(f"{title} {singer}")
    search_queries.append(title)

    seen_urls = set()

    orig_headers = session.headers.copy()
    session.headers.update(DGCOL_HEADERS)

    try:
        for query in search_queries:
            if len(candidates) >= 15:
                break

            try:
                url = f"{DGCOL_BASE}/src/{urllib.parse.quote(query)}"

                resp, err = make_request(session, url, max_retries=2)

                if err or not resp or resp.status_code != 200:
                    continue

                resp.encoding = 'utf-8'
                soup = BeautifulSoup(resp.text, 'html.parser')

                song_items = soup.find_all('a', class_='srcsong-item')

                if not song_items:
                    song_items = soup.find_all('a', href=re.compile(r'/song/\d+'))

                for item in song_items:
                    href = item.get('href', '')

                    song_id_match = re.search(r'/song/(\d+)', href)
                    if not song_id_match:
                        continue

                    song_id = song_id_match.group(1)
                    full_url = f"{DGCOL_BASE}/song/{song_id}"

                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)

                    song_title = ""
                    song_singer = ""

                    name_span = item.find('span', class_='srcsong-name')
                    singer_span = item.find('span', class_='srcsinger-name')

                    if name_span:
                        song_title = name_span.get_text(strip=True)
                    if singer_span:
                        act_span = singer_span.find('span', class_='srcact')
                        if act_span:
                            song_singer = act_span.get_text(strip=True)
                        else:
                            song_singer = singer_span.get_text(strip=True)

                    if not song_title:
                        text = item.get_text(strip=True)
                        text = re.sub(r'歌曲详情', '', text).strip()
                        if ' - ' in text:
                            parts = text.split(' - ', 1)
                            song_title = parts[0].strip()
                            song_singer = parts[1].strip()
                        elif '-' in text:
                            parts = text.split('-', 1)
                            song_title = parts[0].strip()
                            song_singer = parts[1].strip()
                        else:
                            song_title = text

                    if not song_title or len(song_title) < 2:
                        continue

                    title_norm = _normalize_text(title)
                    singer_norm = _normalize_text(singer) if singer else ""
                    st_norm = _normalize_text(song_title)
                    ss_norm = _normalize_text(song_singer)

                    title_score = _title_match_score(title_norm, st_norm)
                    singer_score = _singer_match_score(singer_norm, ss_norm) if singer_norm else 30

                    quality_penalty = _quality_penalty(song_title, song_singer)

                    raw_score = title_score + singer_score - quality_penalty
                    total_score = int(raw_score / 140 * 100)
                    total_score = max(0, min(100, total_score))

                    candidates.append({
                        'title': song_title,
                        'singer': song_singer,
                        'url': full_url,
                        'match_score': total_score,
                        'source': 'dgcol',
                        'song_id': song_id,
                    })

                if candidates:
                    search_method = f"dgcol搜索《{query}》"

            except Exception as e:
                print(f"  dgcol搜索失败: {e}")
                continue
    finally:
        session.headers.clear()
        session.headers.update(orig_headers)

    candidates.sort(key=lambda x: x['match_score'], reverse=True)

    return {
        'candidates': candidates[:15],
        'search_method': search_method,
    }


def dgcol_get_quark_links(session, song_data, quality="flac"):
    """
    获取 dgcol 歌曲的夸克网盘链接

    参数:
        quality: "flac" (无损/高品) 或 "mp3" (普通音质)

    返回: (quark_link, status_message)
    """
    detail_url = song_data.get('url', '')
    if not detail_url:
        return None, "无效的详情页URL"

    try:
        orig_headers = session.headers.copy()
        session.headers.update(DGCOL_HEADERS)

        try:
            session.headers['Referer'] = DGCOL_BASE + '/'
            resp, err = make_request(session, detail_url, max_retries=2)

            if err or not resp or resp.status_code != 200:
                return None, f"访问详情页失败: {err or resp.status_code}"

            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')

            dl_url = None
            if quality == "flac":
                download_links = soup.find_all('a', href=re.compile(r'/msdl/kw\d+\.html?'))
                if download_links:
                    href = download_links[0].get('href', '')
                    if href:
                        dl_url = href if href.startswith('http') else DGCOL_BASE + href

            if not dl_url:
                download_links = soup.find_all('a', href=re.compile(r'/msdl/km\d+\.html?'))
                if download_links:
                    href = download_links[0].get('href', '')
                    if href:
                        dl_url = href if href.startswith('http') else DGCOL_BASE + href

            if not dl_url:
                download_links = soup.find_all('a', href=re.compile(r'/msdl/'))
                if download_links:
                    href = download_links[0].get('href', '')
                    if href:
                        dl_url = href if href.startswith('http') else DGCOL_BASE + href

            if dl_url:
                session.headers['Referer'] = detail_url
                resp2, err2 = make_request(session, dl_url, max_retries=2)
                if not err2 and resp2:
                    final_url = resp2.url
                    if 'pan.quark.cn' in final_url:
                        quark_match = re.search(r'(https?://pan\.quark\.cn/s/[a-zA-Z0-9]+)', final_url)
                        if quark_match:
                            return quark_match.group(1), "成功"

                    dl_content = resp2.text
                    match = re.search(r'window\.location\.href\s*=\s*[\'"](https?://pan\.quark\.cn/s/[a-zA-Z0-9]+)[\'"]', dl_content)
                    if match:
                        return match.group(1), "成功"

                    match2 = re.search(r'(https?://pan\.quark\.cn/s/[a-zA-Z0-9]+)', dl_content)
                    if match2:
                        return match2.group(1), "成功"

                    soup2 = BeautifulSoup(dl_content, 'html.parser')
                    links = soup2.find_all('a', href=re.compile(r'pan\.quark\.cn'))
                    if links:
                        href = links[0].get('href', '')
                        quark_match = re.search(r'(https?://pan\.quark\.cn/s/[a-zA-Z0-9]+)', href)
                        if quark_match:
                            return quark_match.group(1), "成功"

            content = resp.text
            if '404' in content or '不存在' in content or '已失效' in content:
                return None, "页面不存在或已失效"

            return None, "未找到夸克链接"

        finally:
            session.headers.clear()
            session.headers.update(orig_headers)

    except Exception as e:
        return None, f"获取链接异常: {str(e)}"


def dgcol_get_play_url(session, song_data):
    """获取 dgcol 歌曲的在线播放链接"""
    detail_url = song_data.get('url', '')
    if not detail_url:
        return None, "无效的详情页URL"

    try:
        orig_headers = session.headers.copy()
        session.headers.update(DGCOL_HEADERS)

        try:
            session.headers['Referer'] = DGCOL_BASE + '/'
            resp, err = make_request(session, detail_url, max_retries=2)

            if err or not resp or resp.status_code != 200:
                return None, f"访问详情页失败: {err or resp.status_code}"

            resp.encoding = 'utf-8'
            content = resp.text

            match = re.search(r'src\s*=\s*[\'"](https?://[^\'"]+\.(?:ogg|mp3|m4a|flac|wav)[^\'"]*)[\'"]', content, re.I)
            if match:
                return match.group(1), "成功"

            soup = BeautifulSoup(content, 'html.parser')
            audio = soup.find('audio')
            if audio:
                src = audio.get('src') or audio.get('url') or audio.get('data-src')
                if src:
                    return src, "成功"

            return None, "未找到播放链接"

        finally:
            session.headers.clear()
            session.headers.update(orig_headers)

    except Exception as e:
        return None, f"获取播放链接异常: {str(e)}"
