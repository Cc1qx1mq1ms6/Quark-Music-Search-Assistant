# -*- coding: utf-8 -*-
"""
QQ音乐排行榜
"""
import time
import requests

QQ_MUSIC_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://y.qq.com/',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

QQ_TOPLISTS = []

PLATFORM_QQ = 'qq'


def get_qq_toplist_icons():
    """获取QQ音乐榜单图标映射"""
    icons = {
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
        '音乐': '🎵',
        '原创': '✍️',
        'K歌': '🎤',
        '电音': '🎹',
        '说唱': '🎤',
        '摇滚': '🎸',
        '民谣': '🪕',
        '华语': '🇨🇳',
        '粤语': '🎧',
        '英文': '🇬🇧',
        '日韩': '🌏',
        '销量': '📊',
        '关注': '👀',
        '巅峰': '🏆',
        '抖音': '📱',
        '国乐': '🎶',
        '古典': '🎻',
        '校园': '🏫',
        '怀旧': '📼',
        '情歌': '💖',
        '舞曲': '💃',
        'R&B': '🎵',
        '轻音乐': '🎹',
        '儿童': '👶',
        '健身': '💪',
        '国风': '🎋',
        '新国风': '🎋',
    }
    return icons


def _get_icon_for_toplist(name):
    """根据榜单名称获取图标"""
    icons = get_qq_toplist_icons()
    for key, icon in icons.items():
        if key in name:
            return icon
    return '📊'


def qq_get_toplist_list(session=None):
    """
    获取QQ音乐所有榜单列表
    """
    if session is None:
        session = requests.Session()

    url = 'https://c.y.qq.com/v8/fcg-bin/fcg_myqq_toplist.fcg'
    params = {
        'format': 'json',
        'inCharset': 'utf-8',
        'outCharset': 'utf-8',
        'notice': 0,
        'platform': 'h5',
        'needNewCode': 1,
    }

    try:
        resp = session.get(url, headers=QQ_MUSIC_HEADERS, params=params, timeout=15)
        data = resp.json()
        if data.get('code') == 0 and 'data' in data and 'topList' in data['data']:
            result = []
            for item in data['data']['topList']:
                result.append({
                    'id': item.get('id'),
                    'name': item.get('topTitle', ''),
                    'song_count': item.get('songCount', 0),
                    'listen_count': item.get('listenCount', 0),
                    'pic_url': item.get('picUrl', ''),
                    'update_time': item.get('update_time', ''),
                })
            return result, "获取成功"
        return [], f"获取失败: code={data.get('code')}"
    except Exception as e:
        return [], f"请求异常: {str(e)}"


def get_all_qq_toplists(session=None):
    """获取所有QQ音乐排行榜列表"""
    if session is None:
        session = requests.Session()

    toplists, msg = qq_get_toplist_list(session)
    if toplists:
        result = []
        for tl in toplists:
            result.append({
                'id': tl['id'],
                'name': tl['name'],
                'icon': _get_icon_for_toplist(tl['name']),
                'song_count': tl.get('song_count', 0),
                'update_time': tl.get('update_time', ''),
            })
        return result
    return []


def qq_get_toplist_detail(session, topid, limit=50):
    """
    获取指定榜单的歌曲列表

    参数:
        session: requests.Session对象
        topid: 榜单ID
        limit: 返回歌曲数量上限

    返回: (songs_list, status_message)
    """
    url = 'https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg'
    params = {
        'topid': topid,
        'needNewCode': 1,
        'page': 'detail',
        'type': 'top',
        'tpl': 3,
        'platform': 'h5',
        'format': 'json',
    }

    try:
        resp = session.get(url, headers=QQ_MUSIC_HEADERS, params=params, timeout=15)
        data = resp.json()

        if 'songlist' not in data:
            return [], f"获取失败: 无songlist字段"

        songs = []
        for item in data.get('songlist', [])[:limit]:
            s = item.get('data', item)
            singers = [x.get('name', '') for x in s.get('singer', [])]
            singer_str = ', '.join(singers)
            songs.append({
                'songname': s.get('songname', ''),
                'singer': singer_str,
                'singers': singers,
                'albumname': s.get('albumname', ''),
                'songmid': s.get('songmid', ''),
                'songid': s.get('songid', ''),
                'albummid': s.get('albummid', ''),
                'duration': s.get('interval', 0),
            })

        return songs, "获取成功"
    except Exception as e:
        return [], f"请求异常: {str(e)}"


def qq_get_all_recommendations():
    """
    获取所有推荐榜单的数据（用于缓存）

    返回: {
        'update_time': timestamp,
        'update_date': 'YYYY-MM-DD',
        'toplists': [
            {'id': ..., 'name': ..., 'icon': ..., 'songs': [...]}
        ]
    }
    """
    session = requests.Session()
    result = {
        'update_time': time.time(),
        'update_date': time.strftime('%Y-%m-%d'),
        'platform': PLATFORM_QQ,
        'toplists': []
    }

    toplists = get_all_qq_toplists(session)

    if not toplists:
        toplists = [
            {'id': 26, 'name': '热歌榜', 'icon': '🔥'},
            {'id': 27, 'name': '新歌榜', 'icon': '🆕'},
            {'id': 62, 'name': '飙升榜', 'icon': '📈'},
            {'id': 4, 'name': '流行指数榜', 'icon': '⭐'},
            {'id': 5, 'name': '内地榜', 'icon': '🇨🇳'},
            {'id': 6, 'name': '港台榜', 'icon': '🎤'},
            {'id': 3, 'name': '欧美榜', 'icon': '🌍'},
            {'id': 16, 'name': '韩国榜', 'icon': '🇰🇷'},
            {'id': 17, 'name': '日本榜', 'icon': '🇯🇵'},
        ]

    for tl in toplists:
        songs, status = qq_get_toplist_detail(session, tl['id'], limit=30)
        result['toplists'].append({
            'id': tl['id'],
            'name': tl['name'],
            'icon': tl['icon'],
            'songs': songs,
            'status': status,
        })
        time.sleep(0.3)

    return result
