# -*- coding: utf-8 -*-
"""
Apple Music 排行榜
"""
import time
import requests
from bs4 import BeautifulSoup
import json

APPLE_MUSIC_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

PLATFORM_APPLE = 'apple'


def _get_apple_icon(name):
    """根据 Apple Music 榜单名称获取图标"""
    icon_map = {
        '热门': '🔥',
        'Top 100': '🏆',
        'Top 25': '📊',
        '每日': '📅',
        '城市': '🏙️',
        '华语': '🇨🇳',
        '粤语': '🎤',
        '欧美': '🌍',
        '日本': '🇯🇵',
        '韩国': '🇰🇷',
        '流行': '⭐',
        '嘻哈': '🎤',
        '摇滚': '🎸',
        '电子': '🎹',
        '古典': '🎻',
        '爵士': '🎷',
        '乡村': '🤠',
        '民谣': '🪕',
        'R&B': '🎵',
        '情歌': '💖',
        '健身': '💪',
        '睡眠': '🌙',
        '学习': '📚',
        '工作': '💼',
        '派对': '🎉',
        '怀旧': '📼',
        '新歌': '🆕',
        '专辑': '💿',
        'MV': '🎬',
    }
    for key, icon in icon_map.items():
        if key.lower() in name.lower():
            return icon
    return '🍎'


def _extract_page_data(html):
    """从 Apple Music 页面 HTML 中提取 JSON 数据"""
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')
    
    for script in scripts:
        text = script.string or ''
        if len(text) > 10000 and 'topCharts' in text:
            try:
                data = json.loads(text)
                if 'data' in data and isinstance(data['data'], list):
                    return data
            except Exception:
                continue
    return None


def _parse_song_item(item):
    """解析歌曲条目"""
    title = item.get('title', '')
    sub_links = item.get('subtitleLinks') or []
    singers = []
    if sub_links:
        for link in sub_links:
            singer_name = link.get('title', '')
            if singer_name:
                singers.append(singer_name)
    singer_str = ', '.join(singers)
    
    duration = item.get('duration', 0)
    if duration and isinstance(duration, (int, float)):
        if duration > 10000:
            duration = int(duration / 1000)
    
    cd = item.get('contentDescriptor') or {}
    identifiers = cd.get('identifiers') or {}
    song_id = identifiers.get('storeAdamID', '')
    
    return {
        'songname': title,
        'singer': singer_str,
        'singers': singers,
        'albumname': '',
        'songmid': str(song_id),
        'songid': str(song_id),
        'albummid': '',
        'duration': duration,
    }


def _parse_playlist_item(item):
    """解析歌单条目"""
    title_links = item.get('titleLinks') or []
    name = ''
    if title_links and len(title_links) > 0:
        name = title_links[0].get('title', '')
    
    sub_links = item.get('subtitleLinks') or []
    subtitle = ''
    if sub_links and len(sub_links) > 0:
        subtitle = sub_links[0].get('title', '')
    
    cd = item.get('contentDescriptor') or {}
    identifiers = cd.get('identifiers') or {}
    playlist_id = identifiers.get('storeAdamID', '')
    playlist_url = cd.get('url', '')
    
    return {
        'id': str(playlist_id),
        'name': name,
        'subtitle': subtitle,
        'icon': _get_apple_icon(name),
        'url': playlist_url,
    }


def apple_get_top_charts(session=None):
    """
    获取 Apple Music 排行榜首页数据
    
    返回: (toplists, status_message)
    toplists: [{'id': ..., 'name': ..., 'icon': ..., 'songs': [...], 'kind': 'song'/'playlist'}]
    """
    if session is None:
        session = requests.Session()
        session.headers.update(APPLE_MUSIC_HEADERS)
    
    url = 'https://music.apple.com/cn/new/top-charts'
    
    try:
        r = session.get(url, timeout=20)
        r.raise_for_status()
        r.encoding = 'utf-8'
        
        page_data = _extract_page_data(r.text)
        if not page_data:
            return [], '无法提取页面数据'
        
        sections = page_data['data'][0]['data'].get('sections', [])
        result = []
        
        for section in sections:
            items = section.get('items', [])
            if not items:
                continue
            
            header = section.get('header') or {}
            header_item = header.get('item') or {}
            section_title = ''
            
            title_link = header_item.get('titleLink') or {}
            if title_link and 'title' in title_link:
                section_title = title_link['title']
            elif 'title' in header_item:
                section_title = header_item['title']
            elif 'titleLinks' in header_item:
                tl = header_item['titleLinks']
                if isinstance(tl, list) and len(tl) > 0:
                    section_title = tl[0].get('title', '')
            
            first = items[0]
            cd = first.get('contentDescriptor') or {}
            kind = cd.get('kind', 'unknown')
            
            if kind == 'song':
                songs = [_parse_song_item(item) for item in items]
                chart_name = section_title if section_title else '热门歌曲'
                result.append({
                    'id': 'top-songs',
                    'name': chart_name,
                    'icon': _get_apple_icon(chart_name),
                    'kind': 'song',
                    'songs': songs,
                    'song_count': len(songs),
                })
            
            elif kind == 'playlist':
                playlists = [_parse_playlist_item(item) for item in items]
                chart_name = section_title if section_title else '精选歌单'
                result.append({
                    'id': f'playlists-{len(result)}',
                    'name': chart_name,
                    'icon': _get_apple_icon(chart_name),
                    'kind': 'playlist',
                    'playlists': playlists,
                    'playlist_count': len(playlists),
                })
        
        return result, '获取成功'
    
    except Exception as e:
        return [], f'请求异常: {str(e)}'


def apple_get_toplist_detail(session, playlist_id, limit=50, playlist_url=None):
    """
    获取 Apple Music 指定歌单的歌曲列表
    
    参数:
        session: requests.Session对象
        playlist_id: 歌单ID (storeAdamID)
        limit: 返回歌曲数量上限
        playlist_url: 歌单URL（如果提供则直接使用）
    
    返回: (songs_list, status_message)
    """
    if session is None:
        session = requests.Session()
        session.headers.update(APPLE_MUSIC_HEADERS)
    
    if playlist_url:
        url = playlist_url
    else:
        url = f'https://music.apple.com/cn/playlist/x/{playlist_id}'
    
    try:
        r = session.get(url, timeout=20)
        r.raise_for_status()
        r.encoding = 'utf-8'
        
        soup = BeautifulSoup(r.text, 'html.parser')
        scripts = soup.find_all('script')
        
        songs = []
        
        for script in scripts:
            text = script.string or ''
            if len(text) < 1000 or 'PlaylistDetailPageIntent' not in text:
                continue
            
            try:
                data = json.loads(text)
                if 'data' in data and isinstance(data['data'], list):
                    sections = data['data'][0]['data'].get('sections', [])
                    for section in sections:
                        items = section.get('items', [])
                        for item in items:
                            cd = item.get('contentDescriptor') or {}
                            kind = cd.get('kind', '')
                            if kind == 'song':
                                songs.append(_parse_song_item(item))
                                if len(songs) >= limit:
                                    break
                        if len(songs) >= limit:
                            break
                    break
            except Exception:
                continue
        
        if not songs:
            for script in scripts:
                text = script.string or ''
                if len(text) < 100:
                    continue
                
                try:
                    data = json.loads(text)
                    if isinstance(data, dict) and data.get('@type') == 'MusicPlaylist':
                        tracks = data.get('track', [])
                        for track in tracks[:limit]:
                            song_name = track.get('name', '')
                            duration = track.get('duration', 'PT0S')
                            
                            dur_sec = 0
                            if duration and duration.startswith('PT'):
                                import re
                                mins = re.search(r'(\d+)M', duration)
                                secs = re.search(r'(\d+)S', duration)
                                if mins:
                                    dur_sec += int(mins.group(1)) * 60
                                if secs:
                                    dur_sec += int(secs.group(1))
                            
                            songs.append({
                                'songname': song_name,
                                'singer': '',
                                'singers': [],
                                'albumname': '',
                                'songmid': '',
                                'songid': '',
                                'albummid': '',
                                'duration': dur_sec,
                            })
                        break
                except Exception:
                    continue
        
        return songs, '获取成功' if songs else '未找到歌曲数据'
    
    except Exception as e:
        return [], f'请求异常: {str(e)}'


def apple_get_all_recommendations():
    """
    获取所有 Apple Music 排行榜数据（用于缓存）
    
    返回: {
        'update_time': timestamp,
        'update_date': 'YYYY-MM-DD',
        'platform': 'apple',
        'toplists': [
            {'id': ..., 'name': ..., 'icon': ..., 'kind': 'song'/'playlist', 
             'songs': [...]} // 歌曲类型直接有songs
            {'id': ..., 'name': ..., 'icon': ..., 'kind': 'playlist',
             'playlists': [...]} // 歌单类型有playlists列表
        ]
    }
    """
    session = requests.Session()
    session.headers.update(APPLE_MUSIC_HEADERS)
    
    result = {
        'update_time': time.time(),
        'update_date': time.strftime('%Y-%m-%d'),
        'platform': PLATFORM_APPLE,
        'toplists': []
    }
    
    toplists, status = apple_get_top_charts(session)
    
    if not toplists:
        fallback_toplists = [
            {
                'id': 'top-songs',
                'name': '热门歌曲 Top 100',
                'icon': '🔥',
                'kind': 'song',
                'songs': [],
            },
            {
                'id': 'daily-top',
                'name': '每日 Top 100',
                'icon': '📅',
                'kind': 'playlist',
                'playlists': [],
            },
            {
                'id': 'city-top',
                'name': '城市 Top 25',
                'icon': '🏙️',
                'kind': 'playlist',
                'playlists': [],
            },
        ]
        result['toplists'] = fallback_toplists
        return result
    
    for tl in toplists:
        tl_data = {
            'id': tl['id'],
            'name': tl['name'],
            'icon': tl['icon'],
            'kind': tl.get('kind', 'song'),
        }
        
        if tl.get('kind') == 'song':
            tl_data['songs'] = tl.get('songs', [])[:50]
            tl_data['status'] = status
        else:
            tl_data['playlists'] = tl.get('playlists', [])
            tl_data['playlist_count'] = tl.get('playlist_count', 0)
        
        result['toplists'].append(tl_data)
        time.sleep(0.2)
    
    return result
