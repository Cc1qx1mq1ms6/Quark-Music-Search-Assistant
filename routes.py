# -*- coding: utf-8 -*-
"""
API 路由模块
处理所有 HTTP 请求和响应
"""
import os
import json
import requests
from flask import Blueprint, request, jsonify

from search.unified import search_with_source, get_link_for_version, get_play_url_for_version
from search.matching import get_original_singer
from rankings.qq_music import qq_get_toplist_list, qq_get_toplist_detail, PLATFORM_QQ
from rankings.kugou import kugou_get_rank_list, kugou_get_rank_detail, PLATFORM_KUGOU
from rankings.netease import netease_get_rank_list, netease_get_rank_detail, PLATFORM_NETEASE
from rankings.apple_music import apple_get_top_charts, apple_get_toplist_detail, PLATFORM_APPLE

api_bp = Blueprint('api', __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session = requests.Session()


# ============================================
# 搜索相关 API
# ============================================

@api_bp.route('/search', methods=['POST'])
def api_search():
    """搜索歌曲"""
    data = request.json
    title = data.get('title', '').strip()
    singer = data.get('singer', '').strip()
    source = data.get('source', 'gequbao')

    if not title:
        return jsonify({'candidates': [], 'error': '请输入歌曲名'}), 400

    try:
        result = search_with_source(session, title, singer, source=source)
        candidates = result.get('candidates', [])

        original_info = None
        try:
            original = get_original_singer(session, title, singer, candidates)
            if original:
                original_info = {
                    'singer': original.get('singer', ''),
                    'source': original.get('source', '豆瓣音乐')
                }
        except Exception:
            pass

        return jsonify({
            'candidates': candidates,
            'status': result.get('status', ''),
            'original': original_info
        })
    except Exception as e:
        return jsonify({'candidates': [], 'error': str(e)}), 500


@api_bp.route('/get-link', methods=['POST'])
def api_get_link():
    """获取夸克网盘链接"""
    data = request.json
    song = data.get('song', {})
    source = song.get('source', 'gequbao')

    try:
        link, status = get_link_for_version(session, song, source=source)
        if link:
            return jsonify({'link': link, 'status': status})
        else:
            return jsonify({'link': None, 'error': status or '获取链接失败'}), 400
    except Exception as e:
        return jsonify({'link': None, 'error': str(e)}), 500


@api_bp.route('/play', methods=['POST'])
def api_play():
    """获取播放链接"""
    data = request.json
    song = data.get('song', {})

    try:
        url, status = get_play_url_for_version(session, song)
        if url:
            return jsonify({'url': url, 'status': status})
        else:
            return jsonify({'url': None, 'error': status or '获取播放链接失败'}), 400
    except Exception as e:
        return jsonify({'url': None, 'error': str(e)}), 500


@api_bp.route('/search-recommend', methods=['POST'])
def api_search_recommend():
    """搜索推荐页的歌曲"""
    data = request.json
    title = data.get('title', '').strip()
    singer = data.get('singer', '').strip()
    source = data.get('source', 'gequbao')

    if not title:
        return jsonify({'candidates': [], 'error': '请输入歌曲名'}), 400

    try:
        result = search_with_source(session, title, singer, source=source)
        candidates = result.get('candidates', [])
        if candidates:
            song = candidates[0]
            link, status = get_link_for_version(session, song, source=source)
            if link:
                song['quark_link'] = link
                song['link_status'] = status
        return jsonify({'candidates': candidates, 'status': result.get('status', '')})
    except Exception as e:
        return jsonify({'candidates': [], 'error': str(e)}), 500


# ============================================
# 排行榜/推荐 API
# ============================================

@api_bp.route('/toplists')
def api_toplists():
    """获取榜单列表"""
    platform = request.args.get('platform', 'qq')
    
    try:
        if platform == PLATFORM_QQ or platform == 'qq':
            result = qq_get_toplist_list(session)
            toplists = result[0] if isinstance(result, tuple) else result
            return jsonify({'toplists': toplists, 'platform': 'qq'})
        elif platform == PLATFORM_KUGOU or platform == 'kugou':
            result = kugou_get_rank_list(session)
            toplists = result[0] if isinstance(result, tuple) else result
            return jsonify({'toplists': toplists, 'platform': 'kugou'})
        elif platform == PLATFORM_NETEASE or platform == 'netease':
            result = netease_get_rank_list(session)
            toplists = result[0] if isinstance(result, tuple) else result
            return jsonify({'toplists': toplists, 'platform': 'netease'})
        elif platform == PLATFORM_APPLE or platform == 'apple':
            result = apple_get_top_charts(session)
            toplists = result[0] if isinstance(result, tuple) else result
            return jsonify({'toplists': toplists, 'platform': 'apple'})
        else:
            return jsonify({'toplists': [], 'error': '不支持的平台'}), 400
    except Exception as e:
        return jsonify({'toplists': [], 'error': str(e)}), 500


@api_bp.route('/toplist-detail')
def api_toplist_detail():
    """获取榜单详情"""
    platform = request.args.get('platform', 'qq')
    toplist_id = request.args.get('id', '')
    
    try:
        if platform == PLATFORM_QQ or platform == 'qq':
            result = qq_get_toplist_detail(session, toplist_id)
            songs = result[0] if isinstance(result, tuple) else result
            return jsonify({'songs': songs, 'toplist_id': toplist_id})
        elif platform == PLATFORM_KUGOU or platform == 'kugou':
            result = kugou_get_rank_detail(toplist_id, session=session)
            songs = result[0] if isinstance(result, tuple) else result
            return jsonify({'songs': songs, 'toplist_id': toplist_id})
        elif platform == PLATFORM_NETEASE or platform == 'netease':
            result = netease_get_rank_detail(toplist_id, session=session)
            songs = result[0] if isinstance(result, tuple) else result
            return jsonify({'songs': songs, 'toplist_id': toplist_id})
        elif platform == PLATFORM_APPLE or platform == 'apple':
            result = apple_get_toplist_detail(session, toplist_id)
            songs = result[0] if isinstance(result, tuple) else result
            return jsonify({'songs': songs, 'toplist_id': toplist_id})
        else:
            return jsonify({'songs': [], 'error': '不支持的平台'}), 400
    except Exception as e:
        return jsonify({'songs': [], 'error': str(e)}), 500


# 旧版 API 路径兼容
@api_bp.route('/recommend/<platform>')
def api_recommend(platform):
    """获取榜单列表（旧版路径，兼容）"""
    try:
        if platform == PLATFORM_QQ or platform == 'qq':
            result = qq_get_toplist_list(session)
            toplists = result[0] if isinstance(result, tuple) else result
            return jsonify({'toplists': toplists, 'platform': 'qq'})
        elif platform == PLATFORM_KUGOU or platform == 'kugou':
            result = kugou_get_rank_list(session)
            toplists = result[0] if isinstance(result, tuple) else result
            return jsonify({'toplists': toplists, 'platform': 'kugou'})
        elif platform == PLATFORM_NETEASE or platform == 'netease':
            result = netease_get_rank_list(session)
            toplists = result[0] if isinstance(result, tuple) else result
            return jsonify({'toplists': toplists, 'platform': 'netease'})
        elif platform == PLATFORM_APPLE or platform == 'apple':
            result = apple_get_top_charts(session)
            toplists = result[0] if isinstance(result, tuple) else result
            return jsonify({'toplists': toplists, 'platform': 'apple'})
        else:
            return jsonify({'toplists': [], 'error': '不支持的平台'}), 400
    except Exception as e:
        return jsonify({'toplists': [], 'error': str(e)}), 500


@api_bp.route('/recommend/<platform>/<toplist_id>')
def api_recommend_detail(platform, toplist_id):
    """获取榜单详情（旧版路径，兼容）"""
    try:
        if platform == PLATFORM_QQ or platform == 'qq':
            result = qq_get_toplist_detail(session, toplist_id)
            songs = result[0] if isinstance(result, tuple) else result
            return jsonify({'songs': songs, 'toplist_id': toplist_id})
        elif platform == PLATFORM_KUGOU or platform == 'kugou':
            result = kugou_get_rank_detail(toplist_id, session=session)
            songs = result[0] if isinstance(result, tuple) else result
            return jsonify({'songs': songs, 'toplist_id': toplist_id})
        elif platform == PLATFORM_NETEASE or platform == 'netease':
            result = netease_get_rank_detail(toplist_id, session=session)
            songs = result[0] if isinstance(result, tuple) else result
            return jsonify({'songs': songs, 'toplist_id': toplist_id})
        elif platform == PLATFORM_APPLE or platform == 'apple':
            result = apple_get_toplist_detail(session, toplist_id)
            songs = result[0] if isinstance(result, tuple) else result
            return jsonify({'songs': songs, 'toplist_id': toplist_id})
        else:
            return jsonify({'songs': [], 'error': '不支持的平台'}), 400
    except Exception as e:
        return jsonify({'songs': [], 'error': str(e)}), 500


# ============================================
# 歌单 API (保留接口，返回空数据)
# ============================================

@api_bp.route('/playlist-categories')
def api_playlist_categories():
    """获取歌单分类列表"""
    return jsonify({'categories': []})


@api_bp.route('/playlists')
def api_playlists():
    """获取歌单列表"""
    return jsonify({'playlists': []})


# ============================================
# 收藏 API
# ============================================

@api_bp.route('/favorites', methods=['GET', 'POST', 'DELETE'])
def api_favorites():
    """收藏管理"""
    fav_file = os.path.join(BASE_DIR, 'favorites.json')

    if request.method == 'GET':
        try:
            with open(fav_file, 'r', encoding='utf-8') as f:
                favorites = json.load(f)
            return jsonify(favorites)
        except Exception:
            return jsonify([])

    elif request.method == 'POST':
        data = request.json
        try:
            with open(fav_file, 'r', encoding='utf-8') as f:
                favorites = json.load(f)
        except Exception:
            favorites = []

        exists = any(f.get('link') == data.get('link') for f in favorites)
        if not exists:
            favorites.append(data)
            with open(fav_file, 'w', encoding='utf-8') as f:
                json.dump(favorites, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True, 'favorites': favorites})

    elif request.method == 'DELETE':
        data = request.json
        link = data.get('link', '')
        try:
            with open(fav_file, 'r', encoding='utf-8') as f:
                favorites = json.load(f)
            favorites = [f for f in favorites if f.get('link', '') != link]
            with open(fav_file, 'w', encoding='utf-8') as f:
                json.dump(favorites, f, ensure_ascii=False, indent=2)
            return jsonify({'success': True, 'favorites': favorites})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# 批量导出 API
# ============================================

@api_bp.route('/batch-export', methods=['POST'])
def api_batch_export():
    """批量导出歌曲链接"""
    data = request.json
    songs = data.get('songs', [])
    source = data.get('source', 'gequbao')
    
    results = []
    for song in songs:
        try:
            link, status = get_link_for_version(session, song, source=source)
            results.append({
                'song': song,
                'link': link,
                'status': status,
                'success': link is not None
            })
        except Exception as e:
            results.append({
                'song': song,
                'link': None,
                'status': str(e),
                'success': False
            })
    
    return jsonify({'results': results})
