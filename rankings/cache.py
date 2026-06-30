# -*- coding: utf-8 -*-
"""
排行榜缓存管理
支持多平台数据缓存和自动更新
"""
import os
import json
import time

from rankings.qq_music import PLATFORM_QQ
from rankings.kugou import PLATFORM_KUGOU
from rankings.netease import PLATFORM_NETEASE
from rankings.apple_music import PLATFORM_APPLE


def is_cache_valid(cache_data):
    """检查缓存数据是否有效（今天的）"""
    if not cache_data:
        return False
    today = time.strftime('%Y-%m-%d')
    cache_date = cache_data.get('update_date', '')
    return cache_date == today


def load_recommend_cache(cache_file):
    """
    从文件加载排行榜缓存数据

    返回: {
        PLATFORM_QQ: {...},
        PLATFORM_KUGOU: {...},
        PLATFORM_NETEASE: {...},
    }
    """
    result = {
        PLATFORM_QQ: None,
        PLATFORM_KUGOU: None,
        PLATFORM_NETEASE: None,
        PLATFORM_APPLE: None,
    }

    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)

            if isinstance(cached_data, dict):
                if PLATFORM_QQ in cached_data or PLATFORM_KUGOU in cached_data or PLATFORM_APPLE in cached_data:
                    for pf in [PLATFORM_QQ, PLATFORM_KUGOU, PLATFORM_NETEASE, PLATFORM_APPLE]:
                        if cached_data.get(pf):
                            if is_cache_valid(cached_data[pf]):
                                result[pf] = cached_data[pf]
                else:
                    today = time.strftime('%Y-%m-%d')
                    cache_date = cached_data.get('update_date', '')
                    if cache_date == today:
                        result[PLATFORM_QQ] = cached_data
    except Exception:
        pass

    return result


def save_recommend_cache(cache_file, current_platform, new_data, all_data):
    """
    保存排行榜缓存数据到文件

    参数:
        cache_file: 缓存文件路径
        current_platform: 当前平台
        new_data: 新的平台数据
        all_data: 所有平台数据字典
    """
    try:
        save_data = {}
        for pf in [PLATFORM_QQ, PLATFORM_KUGOU, PLATFORM_NETEASE, PLATFORM_APPLE]:
            if all_data.get(pf):
                save_data[pf] = all_data[pf]
        save_data[current_platform] = new_data

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
