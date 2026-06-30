# -*- coding: utf-8 -*-
"""
酷狗音乐排行榜
"""
import time
import requests

KUGOU_BASE = "http://mobilecdn.kugou.com"
KUGOU_RANK_LIST_URL = "http://mobilecdn.kugou.com/api/v3/rank/list?format=json"
KUGOU_RANK_DETAIL_URL = "http://mobilecdn.kugou.com/api/v3/rank/song?rankid={rankid}&page=1&pagesize={pagesize}&json=true"
KUGOU_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

PLATFORM_KUGOU = 'kugou'


def _get_kugou_icon(name):
    icon_map = {
        '飙升': '📈',
        'TOP500': '🏆',
        '流行': '⭐',
        '短视频': '📱',
        '快手': '🎵',
        'DJ': '🎧',
        '内地': '🇨🇳',
        '香港': '🇭🇰',
        '台湾': '🇹🇼',
        '欧美': '🌍',
        '韩国': '🇰🇷',
        '日本': '🇯🇵',
        'ACG': '🎮',
        '电音': '🎹',
        '综艺': '📺',
        '说唱': '🎤',
        '影视': '🎬',
        '粤语': '🎧',
        '原创': '✍️',
        '识曲': '🎵',
        '80后': '📼',
        '90后': '📻',
        '00后': '💿',
        '热歌': '🔥',
        '新歌': '🆕',
        '蜂鸟': '🐦',
        '音乐人': '🎸',
        '金曲': '🏅',
        '国潮': '🎋',
        '民谣': '🎸',
        '纯音乐': '🎹',
        '摇滚': '🎸',
        '古典': '🎻',
        '爵士': '🎷',
        '乡村': '🤠',
        '古风': '🏮',
        '怀旧': '📻',
        '治愈': '💊',
        '中国风': '🏮',
        '网络': '🌐',
        '情歌': '💕',
        '伤感': '😢',
        '快乐': '😊',
        '励志': '💪',
        '校园': '🎓',
        '运动': '⚽',
        '睡前': '🌙',
        '清晨': '🌅',
        '夜店': '🌃',
        '节奏': '🥁',
    }
    for key, icon in icon_map.items():
        if key in name:
            return icon
    return '📊'


def kugou_get_rank_list(session=None):
    if session is None:
        session = requests.Session()
        session.headers.update(KUGOU_HEADERS)

    try:
        r = session.get(KUGOU_RANK_LIST_URL, timeout=15)
        r.raise_for_status()
        data = r.json()

        toplists = []
        if data.get('status') and 'data' in data and 'info' in data['data']:
            for item in data['data']['info']:
                rankname = item.get('rankname', '')
                rankid = item.get('rankid', '')
                if not rankname or not rankid:
                    continue
                icon = _get_kugou_icon(rankname)
                song_count = item.get('extra', {}).get('resp', {}).get('all_total', 0)
                toplists.append({
                    'id': str(rankid),
                    'name': rankname,
                    'icon': icon,
                    'song_count': song_count,
                })

        return toplists, "获取成功"
    except Exception as e:
        return [], f"获取失败: {str(e)}"


def kugou_get_rank_detail(rank_id, limit=30, session=None):
    if session is None:
        session = requests.Session()
        session.headers.update(KUGOU_HEADERS)

    try:
        url = KUGOU_RANK_DETAIL_URL.format(rankid=rank_id, pagesize=limit)
        r = session.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()

        songs = []
        if data.get('status') and 'data' in data and 'info' in data['data']:
            for item in data['data']['info']:
                songname = item.get('songname', '')
                authors = item.get('authors', [])
                singer = ''
                singers = []
                if authors:
                    singers = [a.get('author_name', '') for a in authors if a.get('author_name')]
                    singer = '、'.join(singers)
                if songname:
                    songs.append({
                        'songname': songname,
                        'singer': singer,
                        'singers': singers,
                    })

        return songs, "获取成功"
    except Exception as e:
        return [], f"获取失败: {str(e)}"


def kugou_get_all_recommendations():
    """
    获取酷狗所有排行榜数据（用于缓存）
    """
    session = requests.Session()
    session.headers.update(KUGOU_HEADERS)
    result = {
        'update_time': time.time(),
        'update_date': time.strftime('%Y-%m-%d'),
        'platform': PLATFORM_KUGOU,
        'toplists': []
    }

    toplists, msg = kugou_get_rank_list(session)

    if not toplists:
        toplists = [
            {'id': '8888', 'name': 'TOP500', 'icon': '🏆'},
            {'id': '6666', 'name': '飙升榜', 'icon': '📈'},
            {'id': '59703', 'name': '蜂鸟流行音乐榜', 'icon': '⭐'},
            {'id': '52144', 'name': '短视频热歌榜', 'icon': '📱'},
        ]

    for tl in toplists:
        songs, status = kugou_get_rank_detail(tl['id'], limit=30, session=session)
        result['toplists'].append({
            'id': tl['id'],
            'name': tl['name'],
            'icon': tl['icon'],
            'songs': songs,
            'status': status,
        })
        time.sleep(0.2)

    return result
