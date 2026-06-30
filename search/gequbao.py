# -*- coding: utf-8 -*-
"""
歌曲宝 (gequbao.net) 搜索源
"""
import re
import json
import time
import urllib.parse

from bs4 import BeautifulSoup

from search.utils import HEADERS, make_request, clean_song_title, clean_singer_name, _normalize_text
from search.matching import _singer_match_score, _title_match_score, _quality_penalty


def _do_search(session, title, singer):
    """执行单次搜索，返回候选结果列表"""
    try:
        keyword = f"{title} {singer}" if singer else title
        url = f"https://www.gequbao.net/s/{urllib.parse.quote(keyword)}"

        resp, error = make_request(session, url, max_retries=2, timeout=12)
        if error or resp is None:
            return [], error

        resp.encoding = 'utf-8'
        if resp.status_code != 200:
            return [], f"HTTP {resp.status_code}"

        soup = BeautifulSoup(resp.text, 'html.parser')
        links = soup.find_all('a', href=re.compile(r'search_music\?song_id='))

        if not links:
            return [], "未找到搜索结果"

        seen_ids = set()
        candidates = []

        for link in links:
            href = link.get('href', '')

            song_id_match = re.search(r'song_id=(\d+)', href)
            if not song_id_match:
                continue
            song_id = song_id_match.group(1)
            if song_id in seen_ids:
                continue
            seen_ids.add(song_id)

            title_match = re.search(r'title=([^&]+)', href)
            singer_match = re.search(r'singer=([^&]+)', href)

            result_title = urllib.parse.unquote_plus(title_match.group(1)) if title_match else title
            result_singer = urllib.parse.unquote_plus(singer_match.group(1)) if singer_match else ""

            link_text = link.get_text(strip=True)
            if link_text == '播放&下载' or len(link_text) < 2:
                continue

            singer_score = _singer_match_score(singer, result_singer) if singer else 60
            title_score = _title_match_score(title, result_title)
            penalty = _quality_penalty(result_title, result_singer)

            raw_score = singer_score + title_score - penalty
            total_score = int(raw_score / 140 * 100)
            total_score = max(0, min(100, total_score))

            full_url = href if href.startswith('http') else 'https://www.gequbao.net' + href

            candidates.append({
                'title': result_title.strip(),
                'singer': result_singer.strip(),
                'url': full_url,
                'match_score': total_score,
                'singer_score': singer_score,
                'title_score': title_score,
                'penalty': penalty,
                'source': 'gequbao',
            })

            if len(candidates) >= 12:
                break

        candidates.sort(key=lambda x: x['match_score'], reverse=True)
        return candidates, f"成功（{len(candidates)}个候选）"

    except Exception as e:
        return [], f"错误: {str(e)}"


def search_all_versions(session, title, singer):
    """搜索歌曲的所有版本

    返回 {'candidates': [...], 'status': str, 'search_method': str}
    """
    title_variants = clean_song_title(title)
    singer_variants = clean_singer_name(singer)

    all_candidates = []
    seen_keys = set()

    for t in title_variants[:2]:
        for s in singer_variants[:2]:
            candidates, status = _do_search(session, t, s)
            for c in candidates:
                key = (_normalize_text(c['title']), _normalize_text(c['singer']))
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_candidates.append(c)
            if len(all_candidates) >= 5:
                break
        if len(all_candidates) >= 5:
            break

    if len(all_candidates) < 8:
        for t in title_variants:
            for s in singer_variants[:1]:
                candidates, status = _do_search(session, t, s)
                for c in candidates:
                    key = (_normalize_text(c['title']), _normalize_text(c['singer']))
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_candidates.append(c)
                if len(all_candidates) >= 8:
                    break
            if len(all_candidates) >= 8:
                break

    if len(all_candidates) < 10:
        for t in title_variants[:2]:
            candidates, status = _do_search(session, t, "")
            for c in candidates:
                key = (_normalize_text(c['title']), _normalize_text(c['singer']))
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_candidates.append(c)
            if len(all_candidates) >= 12:
                break

    all_candidates.sort(key=lambda x: x['match_score'], reverse=True)

    if all_candidates:
        return {
            'candidates': all_candidates[:10],
            'status': f"找到 {len(all_candidates)} 个版本",
            'search_method': "多版本搜索"
        }

    return {
        'candidates': [],
        'status': "所有搜索策略均失败",
        'search_method': "全部失败"
    }


def get_mp3_id(session, detail_url):
    """获取mp3_id"""
    for attempt in range(3):
        try:
            resp, error = make_request(session, detail_url, max_retries=2, timeout=15)
            if error or resp is None:
                if attempt < 2:
                    time.sleep(1)
                    continue
                return None, error

            resp.encoding = 'utf-8'
            if resp.status_code != 200:
                if resp.status_code == 500 and attempt < 2:
                    time.sleep(2)
                    continue
                return None, f"HTTP {resp.status_code}"

            patterns = [
                r'window\.mp3_id\s*=\s*[\'"](\d+)[\'"]',
                r'"mp3_id"\s*:\s*(\d+)',
                r'mp3_id[=:]\s*(\d+)',
            ]
            for p in patterns:
                match = re.search(p, resp.text)
                if match:
                    return match.group(1), "成功"

            return None, "未找到mp3_id"

        except Exception as e:
            if attempt < 2:
                time.sleep(1)
                continue
            return None, f"错误: {str(e)}"

    return None, "重试后仍失败"


def get_quark_link(session, mp3_id):
    """获取夸克链接"""
    for attempt in range(3):
        try:
            url = f"https://www.gequbao.net/api/down_url/{mp3_id}"
            resp = session.get(url, allow_redirects=False, timeout=15)

            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get('Location', '')
                if 'pan.quark.cn' in location:
                    return location, "成功（重定向）"

            if resp.status_code == 200:
                patterns = [
                    r'https?://pan\.quark\.cn/s/[a-zA-Z0-9]+',
                    r'pan\.quark\.cn/s/[a-zA-Z0-9]+',
                ]
                for p in patterns:
                    match = re.search(p, resp.text)
                    if match:
                        link = match.group(0)
                        if not link.startswith('http'):
                            link = 'https://' + link
                        return link, "成功（页面提取）"

                try:
                    data = json.loads(resp.text)
                    if isinstance(data, dict):
                        if data.get('code') == 200 and data.get('data'):
                            val = data['data']
                            if isinstance(val, str) and 'pan.quark.cn' in val:
                                return val, "成功（JSON.code200）"
                        for key in ['url', 'link', 'download_url', 'quark_url', 'data']:
                            val = data.get(key, '')
                            if isinstance(val, str) and 'pan.quark.cn' in val:
                                return val, f"成功（JSON.{key}）"
                except:
                    pass

                if 'check_quark_status' in resp.text or '正在跳转' in resp.text or 'queueCount' in resp.text:
                    poll_link, poll_status = _poll_quark_status(session, mp3_id)
                    if poll_link:
                        return poll_link, poll_status

            if attempt < 2:
                time.sleep(1)
                continue

            return None, f"状态码 {resp.status_code}"

        except Exception as e:
            if attempt < 2:
                time.sleep(1)
                continue
            return None, f"错误: {str(e)}"

    return None, "重试后仍失败"


def _poll_quark_status(session, mp3_id, max_polls=10, interval=2):
    """轮询 check_quark_status 接口获取夸克链接"""
    check_url = f"https://www.gequbao.net/api/check_quark_status/{mp3_id}"
    headers_backup = session.headers.get('X-Requested-With', '')
    session.headers['X-Requested-With'] = 'XMLHttpRequest'

    try:
        for i in range(max_polls):
            try:
                resp = session.get(check_url, timeout=15)
                if resp.status_code == 200:
                    try:
                        data = json.loads(resp.text)
                        if data.get('code') == 200:
                            link = data.get('data', '')
                            if link and 'pan.quark.cn' in link:
                                return link, "成功（轮询获取）"
                        elif data.get('code') == 208:
                            pass
                    except:
                        pass
            except:
                pass

            if i < max_polls - 1:
                time.sleep(interval)
    finally:
        if headers_backup:
            session.headers['X-Requested-With'] = headers_backup
        elif 'X-Requested-With' in session.headers:
            del session.headers['X-Requested-With']

    return None, "轮询超时"


def get_play_url(session, detail_url):
    """获取歌曲播放链接（在线预览用）"""
    mp3_id, status = get_mp3_id(session, detail_url)
    if not mp3_id:
        return None, f"获取mp3_id失败: {status}"
    
    try:
        url = f"https://www.gequbao.net/api/down_mp3/{mp3_id}"
        resp = session.get(url, allow_redirects=False, timeout=15)
        
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get('Location', '')
            if location and ('.mp3' in location.lower() or '.m4a' in location.lower()):
                return location, "成功"
        
        return None, f"状态码 {resp.status_code}"
    except Exception as e:
        return None, f"错误: {str(e)}"


def search_single_song(session, title, singer, auto_select=True):
    """搜索单首歌

    auto_select=True: 自动选择最佳版本
    auto_select=False: 返回所有候选版本供用户选择

    返回 {'成功': bool, '夸克链接': str, '原因': str, '候选版本': [...]}
    """
    result = search_all_versions(session, title, singer)
    candidates = result['candidates']

    if not candidates:
        return {
            '成功': False,
            '夸克链接': '',
            '原因': result['status'],
            '候选版本': [],
            '搜索方式': result['search_method']
        }

    if auto_select:
        best = candidates[0]
        mp3_id, mp3_status = get_mp3_id(session, best['url'])

        if not mp3_id:
            return {
                '成功': False,
                '夸克链接': '',
                '原因': f"获取ID失败: {mp3_status}",
                '候选版本': candidates,
                '搜索方式': result['search_method']
            }

        quark_link, quark_status = get_quark_link(session, mp3_id)

        if quark_link:
            return {
                '成功': True,
                '夸克链接': quark_link,
                '原因': '',
                '候选版本': candidates,
                '搜索方式': f"{result['search_method']} - {best['title']} - {best['singer']}",
                '选中版本': best
            }
        else:
            return {
                '成功': False,
                '夸克链接': '',
                '原因': f"获取链接失败: {quark_status}",
                '候选版本': candidates,
                '搜索方式': result['search_method']
            }

    return {
        '成功': False,
        '夸克链接': '',
        '原因': '需要用户选择版本',
        '候选版本': candidates,
        '搜索方式': result['search_method'],
        '需要选择': True
    }


def get_link_for_version(session, candidate):
    """根据用户选择的版本获取夸克链接"""
    mp3_id, mp3_status = get_mp3_id(session, candidate['url'])

    if not mp3_id:
        return None, f"获取ID失败: {mp3_status}"

    quark_link, quark_status = get_quark_link(session, mp3_id)

    if quark_link:
        return quark_link, "成功"
    else:
        return None, f"获取链接失败: {quark_status}"
