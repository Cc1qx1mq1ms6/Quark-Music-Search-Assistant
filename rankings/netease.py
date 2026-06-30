# -*- coding: utf-8 -*-
"""
网易云音乐排行榜
"""
import time
import requests

NETEASE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://music.163.com/',
}

PLATFORM_NETEASE = 'netease'


def _get_netease_icon(name):
    """根据网易云榜单名称获取图标"""
    icon_map = {
        '热歌': '🔥',
        '新歌': '🆕',
        '飙升': '📈',
        '流行': '⭐',
        '内地': '🇨🇳',
        '港台': '🎤',
        '欧美': '🌍',
        '韩国': '🇰🇷',
        '日本': '🇯🇵',
        '影视': '🎬',
        '综艺': '📺',
        '原创': '✍️',
        '说唱': '🎤',
        '古典': '🎻',
        '民谣': '🎸',
        '电音': '🎹',
        'ACG': '🎮',
        '校园': '🎓',
        '睡眠': '🌙',
        '运动': '🏃',
        '驾驶': '🚗',
        '童年': '🧸',
        '浪漫': '💕',
        '治愈': '💊',
        'Rap': '🎤',
        'R&B': '🎷',
        'Jackpot': '🎰',
        '会员': '💎',
    }
    for key, icon in icon_map.items():
        if key.lower() in name.lower():
            return icon
    return '🎵'


def netease_get_rank_list(session=None):
    """获取网易云音乐排行榜列表"""
    if session is None:
        session = requests.Session()
        session.headers.update(NETEASE_HEADERS)

    try:
        r = session.get('https://music.163.com/api/toplist', timeout=15)
        r.raise_for_status()
        data = r.json()

        toplists = []
        if data.get('code') == 200 and 'list' in data:
            for t in data['list']:
                toplists.append({
                    'id': str(t.get('id', '')),
                    'name': t.get('name', '未知'),
                    'icon': _get_netease_icon(t.get('name', '')),
                    'play_count': t.get('playCount', 0),
                    'track_count': t.get('trackCount', 0),
                })

        return toplists, "获取成功"
    except Exception as e:
        return [], f"获取失败: {str(e)}"


def netease_get_rank_detail(rank_id, limit=30, session=None):
    """获取网易云音乐排行榜详情（歌曲列表）"""
    if session is None:
        session = requests.Session()
        session.headers.update(NETEASE_HEADERS)

    try:
        url = f'https://music.163.com/api/playlist/detail?id={rank_id}'
        r = session.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()

        songs = []
        if data.get('code') == 200 and 'result' in data:
            tracks = data['result'].get('tracks', [])
            for idx, t in enumerate(tracks[:limit], 1):
                artists = t.get('artists', []) or t.get('album', {}).get('artists', [])
                singer = artists[0]['name'] if artists else '未知'
                songs.append({
                    'songname': t.get('name', '未知'),
                    'singer': singer,
                    'singers': [a['name'] for a in artists] if artists else [singer],
                })

        return songs, "获取成功"
    except Exception as e:
        return [], f"获取失败: {str(e)}"


def netease_get_all_recommendations():
    """
    获取网易云音乐所有排行榜数据（用于缓存）
    """
    session = requests.Session()
    session.headers.update(NETEASE_HEADERS)
    result = {
        'update_time': time.time(),
        'update_date': time.strftime('%Y-%m-%d'),
        'platform': PLATFORM_NETEASE,
        'toplists': []
    }

    toplists, msg = netease_get_rank_list(session)

    if not toplists:
        toplists = [
            {'id': '3778678', 'name': '云音乐热歌榜', 'icon': '🔥'},
            {'id': '3779629', 'name': '云音乐新歌榜', 'icon': '🆕'},
            {'id': '19723756', 'name': '云音乐飙升榜', 'icon': '📈'},
        ]

    for tl in toplists:
        songs, status = netease_get_rank_detail(tl['id'], limit=30, session=session)
        result['toplists'].append({
            'id': tl['id'],
            'name': tl['name'],
            'icon': tl['icon'],
            'songs': songs,
            'status': status,
        })
        time.sleep(0.2)

    return result
