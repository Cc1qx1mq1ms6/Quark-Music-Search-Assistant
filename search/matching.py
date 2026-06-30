# -*- coding: utf-8 -*-
"""
匹配算法模块
计算歌曲匹配分数、原唱识别等
"""
import re
import json
import urllib.parse
import requests

from search.utils import _normalize_text


def _singer_match_score(search_singer, result_singer):
    """计算歌手匹配分数（0-100）"""
    if not search_singer or not result_singer:
        return 60

    s_norm = _normalize_text(search_singer)
    r_norm = _normalize_text(result_singer)

    if not s_norm or not r_norm:
        return 50

    if s_norm == r_norm:
        return 100

    search_singers = set(s_norm.split())
    result_singers = set(r_norm.split())

    if not search_singers or not result_singers:
        return 50

    common = search_singers & result_singers
    if common:
        if search_singers.issubset(result_singers):
            return 90
        ratio = len(common) / len(search_singers)
        return int(50 + ratio * 40)

    return 30


def _title_match_score(search_title, result_title):
    """计算歌名匹配分数（0-40）"""
    if not search_title or not result_title:
        return 0

    s_norm = _normalize_text(search_title)
    r_norm = _normalize_text(result_title)

    if not s_norm or not r_norm:
        return 0

    if s_norm == r_norm:
        return 40

    if s_norm in r_norm or r_norm in s_norm:
        return 25

    search_words = set(s_norm.split())
    result_words = set(r_norm.split())

    if search_words and result_words:
        common = search_words & result_words
        ratio = len(common) / len(search_words)
        if ratio >= 0.7:
            return 20
        elif ratio >= 0.4:
            return 10

    return 0


def _quality_penalty(title, singer):
    """对低质量内容进行扣分（搬运号、长音频、DJ版等）"""
    penalty = 0
    title_lower = title.lower()
    singer_lower = singer.lower()

    bad_singers = ['宝藏挖掘机', '曦微', '何美汐', '清尘', '潇四月', 'mmgh',
                   '边走边唱', '长音频', '车载音乐', 'dj', 'remix', 'cover']
    for bs in bad_singers:
        if bs.lower() in singer_lower:
            penalty += 20
            break

    bad_title_keywords = ['长音频', '车载', 'dj', '串烧', '翻唱', 'cover',
                          'remix', 'mix', '铃声', '片段', '伴奏', '纯音乐']
    bad_count = sum(1 for kw in bad_title_keywords if kw.lower() in title_lower)
    penalty += bad_count * 10

    if _normalize_text(singer) and _normalize_text(singer) in _normalize_text(title):
        penalty += 15

    return min(penalty, 50)


def calculate_match_score(title, singer, result_title, result_singer):
    """计算综合匹配分数（0-100）"""
    singer_score = _singer_match_score(singer, result_singer) if singer else 60
    title_score = _title_match_score(title, result_title)
    penalty = _quality_penalty(result_title, result_singer)

    raw_score = singer_score + title_score - penalty
    total_score = int(raw_score / 140 * 100)
    total_score = max(0, min(100, total_score))

    return total_score, singer_score, title_score, penalty


def get_original_singer(session, title, singer="", candidates=None):
    """
    获取歌曲的原唱歌手（从豆瓣音乐等权威来源）

    参数:
        session: requests会话
        title: 歌曲名
        singer: 歌手名（可选）
        candidates: 搜索的候选列表（可选，用于当singer为空时推断）

    返回: {'singer': str, 'source': str, 'confidence': float} 或 None
    """
    search_singer = singer
    if not search_singer and candidates:
        for c in candidates[:5]:
            s = c.get('singer', '')
            skip_words = ['宝藏挖掘机', '曦微', '音乐合集', '精选', '合辑', 'dj', 'remix']
            skip = False
            for w in skip_words:
                if w.lower() in s.lower():
                    skip = True
                    break
            if not skip and s:
                search_singer = s
                break

    try:
        search_title = title
        if search_singer:
            search_title = f"{title} {search_singer}"
        url = f"https://music.douban.com/subject_search?search_text={urllib.parse.quote(search_title)}&cat=1003"
        douban_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://music.douban.com/',
        }

        resp = session.get(url, headers=douban_headers, timeout=10)
        if resp.status_code == 200:
            resp.encoding = 'utf-8'

            match = re.search(r'window\.__DATA__\s*=\s*(\{.*?\})\s*;', resp.text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    items = data.get('items', [])

                    if items:
                        best_item = None
                        best_score = 0

                        title_norm = _normalize_text(title)
                        singer_norm = _normalize_text(search_singer) if search_singer else ""

                        for item in items[:15]:
                            item_title = item.get('title', '')
                            abstract = item.get('abstract', '')

                            item_title_norm = _normalize_text(item_title)

                            title_score = 0
                            if title_norm == item_title_norm:
                                title_score = 50
                            elif title_norm in item_title_norm or item_title_norm in title_norm:
                                title_score = 30
                            else:
                                title_words = set(title_norm.split())
                                item_words = set(item_title_norm.split())
                                if title_words and item_words:
                                    common = title_words & item_words
                                    title_score = int(len(common) / max(len(title_words), len(item_words)) * 20)

                            singer_score = 0
                            if singer_norm and abstract:
                                parts = abstract.split(' / ')
                                if parts:
                                    item_singer = _normalize_text(parts[0])
                                    item_singers = [s.strip() for s in re.split(r'[,，]', item_singer)]

                                    for isg in item_singers:
                                        if singer_norm == isg:
                                            singer_score = 60
                                            break
                                        elif singer_norm in isg or isg in singer_norm:
                                            singer_score = 40
                                            break
                                    else:
                                        singer_words = set(singer_norm.split())
                                        for isg in item_singers:
                                            isg_words = set(isg.split())
                                            common = singer_words & isg_words
                                            if len(common) >= len(singer_words) * 0.5:
                                                singer_score = 30
                                                break

                            type_bonus = 0
                            if '单曲' in abstract:
                                type_bonus = 10
                            elif '专辑' in abstract:
                                type_bonus = -20

                            total = title_score + singer_score + type_bonus
                            if total > best_score:
                                best_score = total
                                best_item = item

                        if best_item and best_score >= 40:
                            abstract = best_item.get('abstract', '')
                            parts = abstract.split(' / ')
                            if parts:
                                original_singer = parts[0].strip()
                                return {
                                    'singer': original_singer,
                                    'source': '豆瓣音乐',
                                    'confidence': min(best_score / 120, 1.0)
                                }
                except:
                    pass
    except:
        pass

    return _heuristic_original_singer(title, search_singer or singer)


def _heuristic_original_singer(title, singer):
    """基于启发式规则判断原唱"""
    if not singer:
        return None

    return {
        'singer': singer,
        'source': '启发式判断',
        'confidence': 0.6
    }


def mark_original_versions(candidates, original_singer=None):
    """
    标记候选列表中的原唱版本
    在每个候选中添加 'is_original' 字段
    """
    if not candidates:
        return candidates

    orig_norm = _normalize_text(original_singer) if original_singer else ""

    for c in candidates:
        singer_norm = _normalize_text(c.get('singer', ''))
        title_norm = _normalize_text(c.get('title', ''))

        is_original = False
        reason = ""

        if orig_norm and singer_norm:
            if orig_norm == singer_norm:
                is_original = True
                reason = "歌手完全匹配"
            elif orig_norm in singer_norm or singer_norm in orig_norm:
                is_original = True
                reason = "歌手互相包含"
            else:
                orig_words = set(orig_norm.split())
                singer_words = set(singer_norm.split())
                if orig_words and singer_words:
                    common = orig_words & singer_words
                    if len(common) >= len(orig_words) * 0.6:
                        is_original = True
                        reason = "歌手大部分匹配"

        bad_keywords = ['remix', 'cover', '翻唱', '伴奏', 'dj', 'mix', '版本', 'live']
        for kw in bad_keywords:
            if kw in title_norm:
                if is_original:
                    is_original = False
                    reason = f"歌名含'{kw}'，判定为非原版"
                break

        c['is_original'] = is_original
        if reason:
            c['original_reason'] = reason

    return candidates
