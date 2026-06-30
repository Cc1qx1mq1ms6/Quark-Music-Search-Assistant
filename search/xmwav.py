# -*- coding: utf-8 -*-
"""
xmwav.net 搜索源 - 熊猫无损音乐
"""
import re
import urllib.parse

from bs4 import BeautifulSoup

from search.utils import make_request, _normalize_text
from search.matching import _title_match_score, _singer_match_score, _quality_penalty

XMWAV_BASE = "https://www.xmwav.net"
XMWAV_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://www.xmwav.net/',
}


def _parse_song_list(soup, title, singer):
    """解析歌曲列表"""
    candidates = []
    seen_urls = set()

    articles = soup.find_all('article')

    song_links = []
    if articles:
        for article in articles:
            link = article.find('a', href=re.compile(r'/song/'))
            if link:
                song_links.append(link)
    else:
        song_links = soup.find_all('a', href=re.compile(r'^/song/[\w-]+\.html$'))

    for link in song_links:
        href = link.get('href', '')
        if not href or '/song/' not in href:
            continue

        full_url = href if href.startswith('http') else XMWAV_BASE + href

        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        h3 = link.find(['h3', 'h2', 'h1'])
        song_text = ''
        if h3:
            song_text = h3.get_text(strip=True)
        else:
            song_text = link.get_text(strip=True)
            lines = song_text.split('\n')
            if lines:
                song_text = lines[0].strip()

        title_attr = link.get('title', '')
        if title_attr and not song_text:
            song_text = title_attr.replace('MP3下载', '').replace('_', '').strip()

        song_text = re.sub(r'格式：.*$', '', song_text, flags=re.DOTALL).strip()
        song_text = re.sub(r'大小：.*$', '', song_text, flags=re.DOTALL).strip()

        song_title = song_text
        song_singer = singer

        if '-' in song_text:
            parts = song_text.split('-', 1)
            song_title = parts[0].strip()
            if len(parts) > 1:
                song_singer = parts[1].strip()

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

        song_id = href.split('/')[-1].replace('.html', '')

        candidates.append({
            'title': song_title,
            'singer': song_singer,
            'url': full_url,
            'match_score': total_score,
            'source': 'xmwav',
            'song_id': song_id,
        })

    return candidates


def xmwav_search_all(session, title, singer=""):
    """
    在 xmwav.net 搜索歌曲

    返回: {'candidates': [...], 'search_method': str}
    """
    candidates = []
    search_method = ""

    orig_headers = session.headers.copy()
    session.headers.update(XMWAV_HEADERS)

    try:
        search_queries = []
        if singer:
            search_queries.append(f"{title} {singer}")
        search_queries.append(title)

        seen_urls = set()

        for query in search_queries:
            if len(candidates) >= 15:
                break

            try:
                search_url = f"{XMWAV_BASE}/index/search/"
                data = {
                    'action': '1',
                    'keyword': query,
                }

                session.headers['Referer'] = XMWAV_BASE + '/'
                resp = session.post(search_url, data=data, timeout=15)

                if resp.status_code != 200:
                    continue

                resp.encoding = 'utf-8'
                soup = BeautifulSoup(resp.text, 'html.parser')

                results = _parse_song_list(soup, title, singer)

                for r in results:
                    if r['url'] not in seen_urls:
                        seen_urls.add(r['url'])
                        candidates.append(r)

                if candidates:
                    search_method = f"xmwav搜索《{query}》"

            except Exception as e:
                print(f"  xmwav搜索失败: {e}")
                continue

    finally:
        session.headers.clear()
        session.headers.update(orig_headers)

    candidates.sort(key=lambda x: x['match_score'], reverse=True)

    return {
        'candidates': candidates[:15],
        'search_method': search_method or "xmwav暂未找到匹配结果",
    }


def xmwav_get_quark_links(session, song_data, quality="flac"):
    """
    获取 xmwav 歌曲的夸克网盘链接

    参数:
        quality: "flac" (无损/WAV) 或 "mp3" (普通音质)

    返回: (quark_link, status_message)
    """
    detail_url = song_data.get('url', '')
    if not detail_url:
        return None, "无效的详情页URL"

    try:
        orig_headers = session.headers.copy()
        session.headers.update(XMWAV_HEADERS)

        try:
            session.headers['Referer'] = XMWAV_BASE + '/'
            resp, err = make_request(session, detail_url, max_retries=2)

            if err or not resp or resp.status_code != 200:
                return None, f"访问详情页失败: {err or resp.status_code}"

            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            content = resp.text

            dl_url = None

            if quality == "flac":
                wav_links = soup.find_all('a', href=re.compile(r'/dls/rwk\d+\.html?'))
                if wav_links:
                    href = wav_links[0].get('href', '')
                    if href:
                        dl_url = href if href.startswith('http') else XMWAV_BASE + href

            if not dl_url:
                mp3_links = soup.find_all('a', href=re.compile(r'/dls/rmk\d+\.html?'))
                if mp3_links:
                    href = mp3_links[0].get('href', '')
                    if href:
                        dl_url = href if href.startswith('http') else XMWAV_BASE + href

            if not dl_url:
                all_dl_links = soup.find_all('a', href=re.compile(r'/dls/'))
                if all_dl_links:
                    href = all_dl_links[0].get('href', '')
                    if href:
                        dl_url = href if href.startswith('http') else XMWAV_BASE + href

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

            if '404' in content or '不存在' in content:
                return None, "页面不存在或已失效"

            return None, "未找到夸克链接"

        finally:
            session.headers.clear()
            session.headers.update(orig_headers)

    except Exception as e:
        return None, f"获取链接异常: {str(e)}"


def xmwav_get_play_url(session, song_data):
    """获取 xmwav 歌曲的在线播放链接"""
    detail_url = song_data.get('url', '')
    if not detail_url:
        return None, "无效的详情页URL"

    try:
        orig_headers = session.headers.copy()
        session.headers.update(XMWAV_HEADERS)

        try:
            session.headers['Referer'] = XMWAV_BASE + '/'
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
