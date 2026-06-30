# -*- coding: utf-8 -*-
"""
XM无损音乐 (xmfwav.com) 搜索源
"""
import re
import urllib.parse

from bs4 import BeautifulSoup

from search.utils import make_request, _normalize_text
from search.matching import _title_match_score, _singer_match_score, _quality_penalty

XMFWAV_BASE = "https://www.xmfwav.com"
XMFWAV_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://www.xmfwav.com/',
}


def xmfwav_ensure_session(session):
    """确保 session 有必要的 cookie 和 headers"""
    orig_headers = session.headers.copy()
    session.headers.update(XMFWAV_HEADERS)
    try:
        session.get(f"{XMFWAV_BASE}/", timeout=10)
    except:
        pass
    finally:
        session.headers.clear()
        session.headers.update(orig_headers)


def xmfwav_search_all(session, title, singer=""):
    """
    在 xmfwav.com 搜索歌曲，返回所有候选版本

    返回: {'candidates': [...], 'search_method': str}
    """
    xmfwav_ensure_session(session)

    candidates = []
    search_method = ""

    search_queries = []
    if singer:
        search_queries.append(f"{title} {singer}")
    search_queries.append(title)

    seen_urls = set()

    orig_headers = session.headers.copy()
    session.headers.update(XMFWAV_HEADERS)

    try:
        for query in search_queries:
            if len(candidates) >= 15:
                break

            try:
                url = f"{XMFWAV_BASE}/srcj/?kwd={urllib.parse.quote(query)}"

                resp, err = make_request(session, url, max_retries=2)

                if err or not resp or resp.status_code != 200:
                    continue

                resp.encoding = 'utf-8'
                soup = BeautifulSoup(resp.text, 'html.parser')

                song_list = soup.select_one('.song-list')
                if not song_list:
                    continue

                items = song_list.find_all('a', href=True)

                for item in items:
                    href = item.get('href', '')
                    text = item.get_text(strip=True)

                    if not href or '/song/' not in href:
                        continue

                    full_url = href if href.startswith('http') else XMFWAV_BASE + href

                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)

                    song_text = text.replace('歌曲详情', '').strip()
                    song_title = song_text
                    song_singer = ""

                    if '-' in song_text:
                        parts = song_text.split('-', 1)
                        song_title = parts[0].strip()
                        song_singer = parts[1].strip()

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
                        'source': 'xmfwav',
                        'song_id': href.rstrip('/').split('/')[-1],
                    })

                search_method = f"xmfwav搜索《{query}》"

            except Exception as e:
                print(f"  xmfwav搜索失败: {e}")
                continue
    finally:
        session.headers.clear()
        session.headers.update(orig_headers)

    candidates.sort(key=lambda x: x['match_score'], reverse=True)

    return {
        'candidates': candidates[:15],
        'search_method': search_method,
    }


def xmfwav_get_quark_links(session, song_data, quality="flac"):
    """
    获取 xmfwav 歌曲的夸克网盘链接

    参数:
        quality: "flac" (无损/高品) 或 "mp3" (普通音质)

    返回: (quark_link, status_message)
    """
    detail_url = song_data.get('url', '')
    if not detail_url:
        return None, "无效的详情页URL"

    try:
        orig_headers = session.headers.copy()
        session.headers.update(XMFWAV_HEADERS)

        try:
            session.headers['Referer'] = XMFWAV_BASE + '/'
            resp, err = make_request(session, detail_url, max_retries=2)

            if err or not resp or resp.status_code != 200:
                return None, f"访问详情页失败: {err or resp.status_code}"

            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')

            msdl_links = soup.find_all('a', href=re.compile(r'msdl'))
            flac_href = None
            mp3_href = None

            for a in msdl_links:
                text = a.get_text(strip=True)
                href = a['href']
                if '高品' in text or '无损' in text or 'flac' in text.lower() or 'kw' in href:
                    flac_href = href
                elif 'mp3' in text.lower() or 'km' in href:
                    mp3_href = href

            target_href = flac_href if quality == "flac" else mp3_href
            if not target_href:
                target_href = flac_href or mp3_href

            if not target_href:
                return None, "未找到下载链接"

            download_url = target_href if target_href.startswith('http') else XMFWAV_BASE + target_href
            session.headers['Referer'] = detail_url

            resp2, err2 = make_request(session, download_url, max_retries=2)

            if err2 or not resp2 or resp2.status_code != 200:
                return None, f"访问下载页失败: {err2 or resp2.status_code}"

            resp2.encoding = 'utf-8'
            content = resp2.text
        finally:
            session.headers.clear()
            session.headers.update(orig_headers)

        match = re.search(r"window\.location\.href\s*=\s*['\"](https?://pan\.quark\.cn/s/[a-zA-Z0-9]+)['\"]", content)
        if match:
            return match.group(1), "成功"

        match2 = re.search(r'(https?://pan\.quark\.cn/s/[a-zA-Z0-9]+)', content)
        if match2:
            return match2.group(1), "成功"

        if '404' in content:
            return None, "下载链接已失效"

        return None, "未找到夸克链接"

    except Exception as e:
        return None, f"获取链接异常: {str(e)}"


def xmfwav_get_play_url(session, song_data):
    """获取 xmfwav 歌曲的在线播放链接"""
    detail_url = song_data.get('url', '')
    if not detail_url:
        return None, "无效的详情页URL"

    try:
        orig_headers = session.headers.copy()
        session.headers.update(XMFWAV_HEADERS)

        try:
            session.headers['Referer'] = XMFWAV_BASE + '/'
            resp, err = make_request(session, detail_url, max_retries=2)

            if err or not resp or resp.status_code != 200:
                return None, f"访问详情页失败: {err or resp.status_code}"

            resp.encoding = 'utf-8'
            content = resp.text
        finally:
            session.headers.clear()
            session.headers.update(orig_headers)

        match = re.search(r'url\s*:\s*[\'"](https?://[^\'"]+\.(?:ogg|mp3|m4a|flac|wav)[^\'"]*)[\'"]', content, re.I)
        if match:
            return match.group(1), "成功"

        return None, "未找到播放链接"

    except Exception as e:
        return None, f"获取播放链接异常: {str(e)}"


def xmfwav_search_single(session, title, singer="", quality="flac", auto_select=True):
    """
    xmfwav 单首歌曲搜索（简化版，对应 search_single_song）

    返回: {'title': str, 'singer': str, 'quark_link': str, 'search_method': str, ...}
    """
    result = xmfwav_search_all(session, title, singer)
    candidates = result.get('candidates', [])

    if not candidates:
        return {
            'success': False,
            'error': '未找到匹配的歌曲',
            'candidates': [],
        }

    if not auto_select and len(candidates) > 1:
        return {
            'success': False,
            'error': '多个版本可供选择',
            'candidates': candidates,
            'search_method': result.get('search_method', ''),
        }

    best = candidates[0]

    link, status = xmfwav_get_quark_links(session, best, quality=quality)

    if link:
        best['quark_link'] = link
        best['success'] = True
        best['quality'] = quality
        best['search_method'] = result.get('search_method', '')
        return best
    else:
        return {
            'success': False,
            'error': status,
            'candidates': candidates,
            'search_method': result.get('search_method', ''),
        }
