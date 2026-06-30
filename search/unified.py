# -*- coding: utf-8 -*-
"""
统一搜索接口
封装所有搜索源，提供统一的调用方式
"""

from search.gequbao import search_all_versions as gequbao_search_all
from search.xmfwav import xmfwav_search_all, xmfwav_get_quark_links, xmfwav_get_play_url
from search.dtwav import dtwav_search_all, dtwav_get_quark_links, dtwav_get_play_url
from search.dgcol import dgcol_search_all, dgcol_get_quark_links, dgcol_get_play_url
from search.xmwav import xmwav_search_all, xmwav_get_quark_links, xmwav_get_play_url
from search.gequbao import get_mp3_id, get_quark_link, get_play_url

SOURCE_GEQUBAO = "gequbao"
SOURCE_XMFWAV = "xmfwav"
SOURCE_DTWAV = "dtwav"
SOURCE_DGCOL = "dgcol"
SOURCE_XMWAV = "xmwav"


def search_with_source(session, title, singer="", source=SOURCE_GEQUBAO, quality="flac"):
    """
    根据指定源搜索歌曲

    参数:
        source: "gequbao" / "xmfwav" / "dtwav" / "dgcol"
        quality: "flac" 或 "mp3" (仅无损源有效)
    """
    if source == SOURCE_XMFWAV:
        return xmfwav_search_all(session, title, singer)
    elif source == SOURCE_DTWAV:
        return dtwav_search_all(session, title, singer)
    elif source == SOURCE_DGCOL:
        return dgcol_search_all(session, title, singer)
    elif source == SOURCE_XMWAV:
        return xmwav_search_all(session, title, singer)
    else:
        return gequbao_search_all(session, title, singer)


def get_link_for_version(session, song_data, source=SOURCE_GEQUBAO, quality="flac"):
    """
    根据版本数据获取夸克链接

    参数:
        song_data: 候选版本数据
        source: "gequbao" / "xmfwav" / "dtwav" / "dgcol"
        quality: "flac" 或 "mp3" (仅无损源有效)

    返回: (quark_link, status_message)
    """
    src = song_data.get('source', source)

    if src == 'xmfwav':
        return xmfwav_get_quark_links(session, song_data, quality=quality)
    elif src == 'dtwav':
        return dtwav_get_quark_links(session, song_data, quality=quality)
    elif src == 'dgcol':
        return dgcol_get_quark_links(session, song_data, quality=quality)
    elif src == 'xmwav':
        return xmwav_get_quark_links(session, song_data, quality=quality)
    else:
        detail_url = song_data.get('url', '')
        if not detail_url:
            return None, "无效的详情页URL"

        mp3_id, status = get_mp3_id(session, detail_url)
        if not mp3_id:
            return None, f"获取mp3_id失败: {status}"

        link, status = get_quark_link(session, mp3_id)
        return link, status


def get_play_url_for_version(session, song_data):
    """
    根据版本数据获取在线播放链接

    参数:
        song_data: 候选版本数据

    返回: (play_url, status_message)
    """
    src = song_data.get('source', 'gequbao')

    if src == 'xmfwav':
        return xmfwav_get_play_url(session, song_data)
    elif src == 'dtwav':
        return dtwav_get_play_url(session, song_data)
    elif src == 'dgcol':
        return dgcol_get_play_url(session, song_data)
    elif src == 'xmwav':
        return xmwav_get_play_url(session, song_data)
    else:
        detail_url = song_data.get('url', '')
        if not detail_url:
            return None, "无效的详情页URL"
        return get_play_url(session, detail_url)
