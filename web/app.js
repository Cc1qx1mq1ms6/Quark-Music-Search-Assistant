// ============================================
// 夸克音乐搜索 - Web版 前端逻辑
// ============================================

(function() {

// 简笔画图标辅助函数
function getToplistIconSVG() {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <line x1="8" y1="6" x2="21" y2="6"/>
    <line x1="8" y1="12" x2="21" y2="12"/>
    <line x1="8" y1="18" x2="21" y2="18"/>
    <line x1="3" y1="6" x2="3.01" y2="6"/>
    <line x1="3" y1="12" x2="3.01" y2="12"/>
    <line x1="3" y1="18" x2="3.01" y2="18"/>
  </svg>`;
}

// 状态管理
const appState = {
  currentTab: 'search',
  searchResults: [],
  expandedIndex: -1,
  currentSong: null,
  isPlaying: false,
  currentPlayUrl: '',
  currentVolume: 75,
  isMuted: false,
  isDragging: false,
  favorites: [],
  currentPlatform: 'qq',
  toplists: [],
  selectedToplistIndex: 0,
  toplistSongs: [],
  currentPlaylistCategory: null,
  currentPlaylists: [],
  showBatchExport: false,
  batchStep: 1,
  batchResults: [],
  batchProcessed: 0,
  batchTotal: 0,
  batchSuccess: 0,
  batchFailed: 0,
  isLoadingRecommend: false,
  isMinimized: false
};

// DOM 元素
const audio = document.getElementById('audioPlayer');
const player = document.getElementById('player');
const playIcon = document.getElementById('playIcon');
const pauseIcon = document.getElementById('pauseIcon');
const progressFill = document.getElementById('progressFill');
const progressThumb = document.getElementById('progressThumb');
const progressBar = document.getElementById('progressBar');
const currentTimeEl = document.getElementById('currentTime');
const durationEl = document.getElementById('duration');
const albumArt = document.getElementById('albumArt');
const trackTitle = document.getElementById('trackTitle');
const trackArtist = document.getElementById('trackArtist');
const volumeSlider = document.getElementById('volumeSlider');
const volumeIcon = document.getElementById('volumeIcon');
const muteIcon = document.getElementById('muteIcon');
const resultList = document.getElementById('resultList');
const resultCount = document.getElementById('resultCount');
const toplistList = document.getElementById('toplistList');
const toplistSongsEl = document.getElementById('toplistSongs');
const currentToplistName = document.getElementById('currentToplistName');
const toplistCount = document.getElementById('toplistCount');
const favoritesList = document.getElementById('favoritesList');
const batchDialog = document.getElementById('batchDialog');

// 初始化音量
audio.volume = 0.75;

// 从本地存储加载收藏
function loadFavorites() {
  try {
    const saved = localStorage.getItem('favorites');
    if (saved) {
      appState.favorites = JSON.parse(saved);
    }
  } catch (e) {
    appState.favorites = [];
  }
}

// 保存收藏到本地存储
function saveFavorites() {
  localStorage.setItem('favorites', JSON.stringify(appState.favorites));
}

// 格式化时间
function formatTime(seconds) {
  if (isNaN(seconds)) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// ============================================
// 标签页切换
// ============================================

function switchTab(tab) {
  appState.currentTab = tab;
  
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tab);
  });
  
  document.querySelectorAll('.bottom-nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tab);
  });
  
  const searchView = document.getElementById('searchView');
  const recommendView = document.getElementById('recommendView');
  const favoritesView = document.getElementById('favoritesView');
  
  searchView.style.display = 'none';
  searchView.classList.remove('active-view');
  recommendView.style.display = 'none';
  recommendView.classList.remove('active-view');
  favoritesView.style.display = 'none';
  
  if (tab === 'search') {
    if (isMobile()) {
      searchView.classList.add('active-view');
    } else {
      searchView.style.display = 'grid';
    }
  } else if (tab === 'recommend') {
    if (isMobile()) {
      recommendView.classList.add('active-view');
    } else {
      recommendView.style.display = 'grid';
    }
  } else if (tab === 'favorites') {
    favoritesView.style.display = 'flex';
  }
  
  if (tab === 'recommend' && appState.toplists.length === 0) {
    loadRecommend();
  }
  
  if (tab === 'favorites') {
    renderFavorites();
  }
}

// ============================================
// 搜索功能
// ============================================

async function doSearch() {
  const title = document.getElementById('searchTitle').value.trim();
  const singer = document.getElementById('searchSinger').value.trim();
  const source = document.getElementById('searchSource').value;
  
  if (!title) {
    alert('请输入歌曲名');
    return;
  }
  
  const searchBtn = document.getElementById('searchBtn');
  searchBtn.disabled = true;
  searchBtn.innerHTML = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:18px;height:18px;animation: spin 1s linear infinite;">
      <circle cx="12" cy="12" r="10"/>
      <path d="M12 6v6l4 2"/>
    </svg>
    搜索中...
  `;
  
  resultList.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <div class="loading-text">正在搜索...</div>
    </div>
  `;
  
  try {
    const response = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, singer, source })
    });
    
    const data = await response.json();
    appState.searchResults = data.candidates || [];
    
    // 更新原唱信息
    if (data.original) {
      document.getElementById('originalInfoSection').style.display = 'block';
      document.getElementById('originalSinger').textContent = data.original.singer;
      document.getElementById('originalSource').textContent = `来源：${data.original.source}`;
    } else {
      document.getElementById('originalInfoSection').style.display = 'none';
    }
    
    renderSearchResults();
  } catch (error) {
    console.error('搜索失败:', error);
    resultList.innerHTML = `
      <div class="empty-state">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width: 64px; height: 64px;">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <div class="empty-text">搜索失败，请重试</div>
      </div>
    `;
  } finally {
    searchBtn.disabled = false;
    searchBtn.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:18px;height:18px;">
        <circle cx="11" cy="11" r="8"/>
        <path d="M21 21l-4.35-4.35"/>
      </svg>
      搜索
    `;
  }
}

function renderSearchResults() {
  const results = appState.searchResults;
  resultCount.textContent = `找到 ${results.length} 首`;
  
  if (results.length === 0) {
    resultList.innerHTML = `
      <div class="empty-state">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width: 64px; height: 64px;">
          <circle cx="11" cy="11" r="8"/>
          <path d="M21 21l-4.35-4.35"/>
        </svg>
        <div class="empty-text">没有找到相关歌曲</div>
      </div>
    `;
    return;
  }
  
  resultList.innerHTML = results.map((song, index) => {
    const isExpanded = appState.expandedIndex === index;
    const isOriginal = song.is_original;
    const matchScore = song.match_score || 0;
    let matchClass = 'low';
    if (matchScore >= 100) matchClass = 'high';
    else if (matchScore >= 80) matchClass = 'medium';
    
    return `
      <div class="song-item ${isExpanded ? 'expanded' : ''}" onclick="toggleExpandSong(${index})">
        <div class="song-main">
          <div class="song-index">${index + 1}</div>
          <div class="song-cover">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 18V5l12-2v13" style="stroke-width: 1.8;"/>
              <circle cx="6" cy="18" r="3" style="stroke-width: 1.5;"/>
              <circle cx="18" cy="16" r="3" style="stroke-width: 1.5;"/>
            </svg>
          </div>
          <div class="song-info">
            <div class="song-title">
              ${song.title}
              ${isOriginal ? '<span class="original-badge">原唱</span>' : ''}
            </div>
            <div class="song-singer">${song.singer}</div>
            <div class="song-match ${matchClass}">匹配度: ${matchScore}%</div>
          </div>
          <button class="song-play-btn" onclick="event.stopPropagation(); playSong(${index})" title="播放">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="5 3 19 12 5 21 5 3" fill="currentColor" stroke="none" style="opacity: 0.9;"/>
            </svg>
          </button>
        </div>
        <div class="song-details" id="songDetails-${index}">
          ${song.quark_link ? `
            <div class="link-box">${song.quark_link}</div>
            <div class="actions">
              <button class="action-btn play-btn" onclick="event.stopPropagation(); playSong(${index})">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="5 3 19 12 5 21 5 3" fill="currentColor" stroke="none"/>
                </svg>
                播放
              </button>
              <button class="action-btn" onclick="event.stopPropagation(); copyLink('${song.quark_link}')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke-width="1.5"/>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke-width="1.5"/>
                </svg>
                复制
              </button>
              <button class="action-btn" onclick="event.stopPropagation(); openLink('${song.quark_link}')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                  <polyline points="15 3 21 3 21 9" stroke-width="1.5"/>
                  <line x1="10" y1="14" x2="21" y2="3" stroke-width="1.5"/>
                </svg>
                打开
              </button>
              <button class="action-btn" onclick="event.stopPropagation(); toggleFavorite(${index})">
                <svg viewBox="0 0 24 24" fill="${isFavorited(song) ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                </svg>
                ${isFavorited(song) ? '已收藏' : '收藏'}
              </button>
            </div>
          ` : song.loading ? `
            <div class="detail-loading">
              <div class="spinner" style="margin: 0 auto 12px; width: 24px; height: 24px;"></div>
              正在获取夸克链接...
            </div>
          ` : song.error ? `
            <div class="detail-error">❌ ${song.error}</div>
          ` : ''}
        </div>
      </div>
    `;
  }).join('');
}

async function toggleExpandSong(index) {
  if (appState.expandedIndex === index) {
    appState.expandedIndex = -1;
  } else {
    appState.expandedIndex = index;
    
    // 如果没有夸克链接且未在加载，开始获取
    const song = appState.searchResults[index];
    if (!song.quark_link && !song.loading && !song.error) {
      song.loading = true;
      renderSearchResults();
      
      try {
        const response = await fetch('/api/get-link', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ song })
        });
        
        const data = await response.json();
        if (data.link) {
          song.quark_link = data.link;
        } else {
          song.error = data.error || '获取链接失败';
        }
      } catch (error) {
        song.error = '获取链接失败';
      } finally {
        song.loading = false;
        renderSearchResults();
      }
    }
  }
  
  renderSearchResults();
}

// ============================================
// 播放器功能
// ============================================

async function playSong(index) {
  const song = appState.searchResults[index];
  if (!song) return;
  
  appState.currentSong = song;
  trackTitle.textContent = song.title;
  trackArtist.textContent = song.singer;
  
  // 如果已有播放URL，直接播放
  if (song.play_url) {
    appState.currentPlayUrl = song.play_url;
    audio.src = song.play_url;
    audio.play();
    return;
  }
  
  // 否则获取播放URL
  try {
    const response = await fetch('/api/play', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ song })
    });
    
    const data = await response.json();
    if (data.url) {
      song.play_url = data.url;
      appState.currentPlayUrl = data.url;
      audio.src = data.url;
      audio.play();
    } else {
      alert('无法获取播放链接');
    }
  } catch (error) {
    console.error('播放失败:', error);
    alert('播放失败，请重试');
  }
}

function togglePlay() {
  if (!appState.currentSong) {
    if (appState.searchResults.length > 0) {
      playSong(0);
    }
    return;
  }
  
  if (audio.paused) {
    audio.play();
  } else {
    audio.pause();
  }
}

function updatePlayPauseButton() {
  if (appState.isPlaying) {
    playIcon.style.display = 'none';
    pauseIcon.style.display = 'block';
    albumArt.classList.add('spinning');
  } else {
    playIcon.style.display = 'block';
    pauseIcon.style.display = 'none';
    albumArt.classList.remove('spinning');
  }
}

function prevSong() {
  if (appState.searchResults.length === 0) return;
  
  let currentIndex = appState.searchResults.findIndex(s => s === appState.currentSong);
  let prevIndex = currentIndex - 1;
  if (prevIndex < 0) prevIndex = appState.searchResults.length - 1;
  playSong(prevIndex);
}

function nextSong() {
  if (appState.searchResults.length === 0) return;
  
  let currentIndex = appState.searchResults.findIndex(s => s === appState.currentSong);
  let nextIndex = currentIndex + 1;
  if (nextIndex >= appState.searchResults.length) nextIndex = 0;
  playSong(nextIndex);
}

function toggleMute() {
  if (appState.isMuted) {
    audio.volume = appState.currentVolume / 100;
    volumeSlider.value = appState.currentVolume;
    volumeIcon.style.display = 'block';
    muteIcon.style.display = 'none';
  } else {
    audio.volume = 0;
    volumeSlider.value = 0;
    volumeIcon.style.display = 'none';
    muteIcon.style.display = 'block';
  }
  appState.isMuted = !appState.isMuted;
}

function togglePlayerMinimize() {
  appState.isMinimized = !appState.isMinimized;
  player.classList.toggle('minimized', appState.isMinimized);
  const playerExpandBtn = document.getElementById('playerExpandBtn');
  if (playerExpandBtn) {
    playerExpandBtn.style.display = appState.isMinimized ? 'flex' : 'none';
  }
}

// 进度条交互
function updateProgress(e) {
  const rect = progressBar.getBoundingClientRect();
  let percent = (e.clientX - rect.left) / rect.width;
  percent = Math.max(0, Math.min(1, percent));
  
  progressFill.style.width = (percent * 100) + '%';
  progressThumb.style.left = (percent * 100) + '%';
  
  if (audio.duration) {
    currentTimeEl.textContent = formatTime(percent * audio.duration);
  }
  
  return percent;
}

progressBar.addEventListener('mousedown', function(e) {
  appState.isDragging = true;
  progressBar.classList.add('dragging');
  updateProgress(e);
});

document.addEventListener('mousemove', function(e) {
  if (appState.isDragging) {
    updateProgress(e);
  }
});

document.addEventListener('mouseup', function(e) {
  if (appState.isDragging) {
    const percent = updateProgress(e);
    if (audio.duration) {
      audio.currentTime = percent * audio.duration;
    }
    appState.isDragging = false;
    progressBar.classList.remove('dragging');
  }
});

// 触摸支持
progressBar.addEventListener('touchstart', function(e) {
  appState.isDragging = true;
  progressBar.classList.add('dragging');
  updateProgress(e.touches[0]);
});

document.addEventListener('touchmove', function(e) {
  if (appState.isDragging) {
    updateProgress(e.touches[0]);
  }
});

document.addEventListener('touchend', function(e) {
  if (appState.isDragging) {
    const percent = parseFloat(progressFill.style.width) / 100;
    if (audio.duration) {
      audio.currentTime = percent * audio.duration;
    }
    appState.isDragging = false;
    progressBar.classList.remove('dragging');
  }
});

// 音量控制
volumeSlider.addEventListener('input', function() {
  const volume = this.value;
  appState.currentVolume = volume;
  audio.volume = volume / 100;
  
  if (volume == 0) {
    appState.isMuted = true;
    volumeIcon.style.display = 'none';
    muteIcon.style.display = 'block';
  } else {
    appState.isMuted = false;
    volumeIcon.style.display = 'block';
    muteIcon.style.display = 'none';
  }
});

// 音频事件
audio.addEventListener('timeupdate', function() {
  if (!appState.isDragging && audio.duration) {
    const progress = (audio.currentTime / audio.duration) * 100;
    progressFill.style.width = progress + '%';
    progressThumb.style.left = progress + '%';
    currentTimeEl.textContent = formatTime(audio.currentTime);
  }
});

audio.addEventListener('loadedmetadata', function() {
  durationEl.textContent = formatTime(audio.duration);
});

audio.addEventListener('ended', function() {
  nextSong();
});

audio.addEventListener('play', function() {
  appState.isPlaying = true;
  updatePlayPauseButton();
});

audio.addEventListener('pause', function() {
  appState.isPlaying = false;
  updatePlayPauseButton();
});

// ============================================
// 推荐功能
// ============================================

async function loadRecommend() {
  if (appState.isLoadingRecommend) return;
  
  appState.isLoadingRecommend = true;
  
  try {
    const response = await fetch(`/api/recommend/${appState.currentPlatform}`);
    const data = await response.json();
    appState.toplists = data.toplists || [];
    
    renderToplists();
    
    if (appState.toplists.length > 0) {
      selectToplist(0);
    }
  } catch (error) {
    console.error('加载推荐失败:', error);
    toplistList.innerHTML = `
      <div class="empty-state" style="padding: 40px 20px;">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width: 64px; height: 64px;">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <div class="empty-text">加载失败</div>
      </div>
    `;
  } finally {
    appState.isLoadingRecommend = false;
  }
}

function refreshRecommend() {
  appState.toplists = [];
  appState.toplistSongs = [];
  loadRecommend();
}

function switchPlatform(platform) {
  appState.currentPlatform = platform;
  appState.toplists = [];
  appState.toplistSongs = [];
  
  document.querySelectorAll('.platform-btn').forEach((btn, idx) => {
    const platforms = ['qq', 'kugou', 'netease', 'apple'];
    btn.classList.toggle('active', platforms[idx] === platform);
  });
  
  loadRecommend();
}

function renderToplists() {
  if (appState.toplists.length === 0) {
    toplistList.innerHTML = `
      <div class="empty-state" style="padding: 40px 20px;">
        <div class="empty-icon">📊</div>
        <div class="empty-text">暂无榜单</div>
      </div>
    `;
    return;
  }
  
  if (isMobile()) {
    toplistList.innerHTML = appState.toplists.map((list, index) => `
      <div class="toplist-item ${index === appState.selectedToplistIndex ? 'active' : ''}" onclick="selectToplist(${index})">
        <div class="toplist-item-header">
          <span class="toplist-item-name">${list.name}</span>
          <span class="toplist-item-count">${list.song_count || list.track_count || (list.songs ? list.songs.length : 0) || '--'} 首</span>
        </div>
      </div>
    `).join('');
    return;
  }
  
  toplistList.innerHTML = appState.toplists.map((list, index) => `
    <div class="toplist-item ${index === appState.selectedToplistIndex ? 'active' : ''}" onclick="selectToplist(${index})">
      <span class="toplist-icon">${getToplistIconSVG()}</span>
      <div class="toplist-info">
        <div class="toplist-name">${list.name}</div>
        <div class="toplist-count">${list.song_count || list.track_count || (list.songs ? list.songs.length : 0) || '--'} 首</div>
      </div>
    </div>
  `).join('');
}

async function selectToplist(index) {
  appState.selectedToplistIndex = index;
  const toplist = appState.toplists[index];
  
  if (!toplist) return;
  
  currentToplistName.textContent = toplist.name;
  
  renderToplists();
  
  if (toplist.kind === 'playlist' && toplist.playlists && toplist.playlists.length > 0) {
    appState.currentPlaylistCategory = toplist;
    appState.currentPlaylists = toplist.playlists;
    appState.toplistSongs = [];
    renderPlaylistList();
    return;
  }
  
  appState.currentPlaylistCategory = null;
  appState.currentPlaylists = [];
  
  if (toplist.songs && toplist.songs.length > 0) {
    appState.toplistSongs = toplist.songs;
    renderToplistSongs();
    return;
  }
  
  toplistSongsEl.innerHTML = `
    <div class="loading-state" style="grid-column: 1 / -1;">
      <div class="spinner"></div>
      <div class="loading-text">加载中...</div>
    </div>
  `;
  
  try {
    const response = await fetch(`/api/recommend/${appState.currentPlatform}/${toplist.id}`);
    const data = await response.json();
    toplist.songs = data.songs || [];
    toplist.song_count = toplist.songs.length;
    appState.toplistSongs = toplist.songs;
    renderToplistSongs();
    renderToplists();
  } catch (error) {
    console.error('加载榜单详情失败:', error);
    toplistSongsEl.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width: 64px; height: 64px;">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <div class="empty-text">加载失败</div>
      </div>
    `;
  }
}

function renderPlaylistList() {
  const playlists = appState.currentPlaylists;
  toplistCount.textContent = `${playlists.length} 个歌单`;
  
  if (playlists.length === 0) {
    toplistSongsEl.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <div class="empty-icon">📋</div>
        <div class="empty-text">暂无歌单</div>
      </div>
    `;
    return;
  }
  
  toplistSongsEl.innerHTML = playlists.map((pl, index) => `
    <div class="toplist-song playlist-item" onclick="loadApplePlaylist(${index})">
      <div class="playlist-icon">${pl.icon || '📋'}</div>
      <div class="toplist-song-info">
        <div class="toplist-song-title">${pl.name}</div>
        <div class="toplist-song-singer">${pl.subtitle || 'Apple Music'}</div>
      </div>
      <span class="playlist-arrow">▶</span>
    </div>
  `).join('');
}

async function loadApplePlaylist(index) {
  const pl = appState.currentPlaylists[index];
  if (!pl) return;
  
  currentToplistName.textContent = pl.name;
  toplistCount.textContent = '加载中...';
  
  toplistSongsEl.innerHTML = `
    <div class="loading-state" style="grid-column: 1 / -1;">
      <div class="spinner"></div>
      <div class="loading-text">加载中...</div>
    </div>
  `;
  
  try {
    const response = await fetch(`/api/recommend/${appState.currentPlatform}/${pl.id}`);
    const data = await response.json();
    const songs = data.songs || [];
    appState.toplistSongs = songs;
    renderToplistSongs();
  } catch (error) {
    console.error('加载歌单失败:', error);
    toplistSongsEl.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width: 64px; height: 64px;">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <div class="empty-text">加载失败</div>
      </div>
    `;
  }
}

function isMobile() {
  return window.innerWidth <= 850;
}

function renderToplistSongs() {
  const songs = appState.toplistSongs;
  const toplist = appState.toplists[appState.selectedToplistIndex];
  
  if (isMobile()) {
    if (songs.length === 0) {
      toplistSongsEl.innerHTML = `
        <div class="toplist-card">
          <div class="toplist-card-header">
            <div class="toplist-card-title">
              <span class="icon">${getToplistIconSVG()}</span>
              <span class="name">${toplist?.name || '暂无榜单'}</span>
            </div>
            <span class="toplist-card-count">0 首</span>
          </div>
          <div class="empty-state" style="padding: 30px 0; text-align: center;">
            <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width: 48px; height: 48px;">
              <path d="M9 18V5l12-2v13"/>
              <circle cx="6" cy="18" r="3"/>
              <circle cx="18" cy="16" r="3"/>
            </svg>
            <div class="empty-text">暂无歌曲</div>
          </div>
        </div>
      `;
      return;
    }
    
    toplistSongsEl.innerHTML = `
      <div class="toplist-card">
        <div class="toplist-card-header">
          <div class="toplist-card-title">
            <span class="icon">${getToplistIconSVG()}</span>
            <span class="name">${toplist?.name || '榜单'}</span>
          </div>
          <span class="toplist-card-count">${songs.length} 首</span>
        </div>
        ${songs.map((song, index) => `
          <div class="toplist-song">
            <div class="toplist-song-rank top3 ${index === 0 ? 'rank1' : index === 1 ? 'rank2' : index === 2 ? 'rank3' : ''}">${index + 1}</div>
            <div class="toplist-song-info">
              <div class="toplist-song-title">${song.songname || song.title}</div>
              <div class="toplist-song-singer">${song.singer || song.artist}</div>
            </div>
            <button class="toplist-song-search" onclick="searchRecommendSong(${index})">🔍 搜</button>
          </div>
        `).join('')}
      </div>
    `;
    return;
  }
  
  toplistCount.textContent = `${songs.length} 首`;
  
  if (songs.length === 0) {
    toplistSongsEl.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <div class="empty-icon">🎵</div>
        <div class="empty-text">暂无歌曲</div>
      </div>
    `;
    return;
  }
  
  toplistSongsEl.innerHTML = songs.map((song, index) => `
    <div class="toplist-song">
      <div class="toplist-song-index">${index + 1}</div>
      <div class="toplist-song-info">
        <div class="toplist-song-title">${song.songname || song.title}</div>
        <div class="toplist-song-singer">${song.singer || song.artist}</div>
      </div>
      <button class="toplist-search-btn" onclick="searchRecommendSong(${index})">🔍 搜索</button>
    </div>
  `).join('');
}

function searchRecommendSong(index) {
  const song = appState.toplistSongs[index];
  if (!song) return;
  
  document.getElementById('searchTitle').value = song.songname || song.title || '';
  document.getElementById('searchSinger').value = song.singer || song.artist || '';
  switchTab('search');
  doSearch();
}

// ============================================
// 收藏功能
// ============================================

function isFavorited(song) {
  return appState.favorites.some(f => f.title === song.title && f.singer === song.singer);
}

function toggleFavorite(index) {
  const song = appState.searchResults[index];
  if (!song) return;
  
  const favIndex = appState.favorites.findIndex(f => f.title === song.title && f.singer === song.singer);
  
  if (favIndex > -1) {
    appState.favorites.splice(favIndex, 1);
  } else {
    appState.favorites.push({
      title: song.title,
      singer: song.singer,
      link: song.quark_link || '',
      source: song.source || 'gequbao'
    });
  }
  
  saveFavorites();
  renderSearchResults();
  
  if (appState.currentTab === 'favorites') {
    renderFavorites();
  }
}

function renderFavorites() {
  if (appState.favorites.length === 0) {
    favoritesList.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width: 64px; height: 64px;">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
        <div class="empty-text">还没有收藏的歌曲</div>
      </div>
    `;
    return;
  }
  
  favoritesList.innerHTML = appState.favorites.map((song, index) => `
    <div class="favorite-item">
      <div class="favorite-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 18V5l12-2v13"/>
          <circle cx="6" cy="18" r="3"/>
          <circle cx="18" cy="16" r="3"/>
        </svg>
      </div>
      <div class="favorite-info">
        <div class="favorite-title">${song.title}</div>
        <div class="favorite-singer">${song.singer}</div>
      </div>
      <div class="favorite-actions">
        <button class="fav-btn" title="复制链接" onclick="copyLink('${song.link}')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
          </svg>
        </button>
        <button class="fav-btn" title="打开链接" onclick="openLink('${song.link}')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
            <polyline points="15 3 21 3 21 9"/>
            <line x1="10" y1="14" x2="21" y2="3"/>
          </svg>
        </button>
        <button class="fav-btn" title="取消收藏" onclick="removeFavorite(${index})">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
        </button>
      </div>
    </div>
  `).join('');
}

function removeFavorite(index) {
  appState.favorites.splice(index, 1);
  saveFavorites();
  renderFavorites();
}

function exportFavorites() {
  if (appState.favorites.length === 0) {
    alert('还没有收藏的歌曲');
    return;
  }
  
  const content = appState.favorites.map(f => 
    `${f.title} - ${f.singer}\n${f.link}`
  ).join('\n\n');
  
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '收藏歌曲.txt';
  a.click();
  URL.revokeObjectURL(url);
}

function clearFavorites() {
  if (!confirm('确定要清空所有收藏吗？')) return;
  appState.favorites = [];
  saveFavorites();
  renderFavorites();
}

function toggleFavorites() {
  switchTab('favorites');
}

// ============================================
// 批量导出
// ============================================

function toggleBatchExport() {
  appState.showBatchExport = !appState.showBatchExport;
  batchDialog.style.display = appState.showBatchExport ? 'flex' : 'none';
  
  if (appState.showBatchExport) {
    resetBatchExport();
  }
}

function resetBatchExport() {
  appState.batchStep = 1;
  appState.batchResults = [];
  appState.batchProcessed = 0;
  appState.batchTotal = 0;
  appState.batchSuccess = 0;
  appState.batchFailed = 0;
  
  document.getElementById('batchContent').value = '';
  updateBatchSteps();
  document.getElementById('batchStep1Content').style.display = 'block';
  document.getElementById('batchStep2Content').style.display = 'none';
  document.getElementById('batchStep3Content').style.display = 'none';
}

function updateBatchSteps() {
  for (let i = 1; i <= 3; i++) {
    const step = document.getElementById(`batchStep${i}`);
    step.classList.remove('active', 'done');
    if (i < appState.batchStep) step.classList.add('done');
    else if (i === appState.batchStep) step.classList.add('active');
  }
}

function startBatchExport() {
  const content = document.getElementById('batchContent').value.trim();
  if (!content) {
    alert('请输入歌单内容');
    return;
  }
  
  // 解析歌单
  const lines = content.split('\n').filter(line => line.trim());
  const songs = [];
  
  for (const line of lines) {
    const parts = line.split(/[-–—]/);
    const title = parts[0].replace(/^\d+\.\s*/, '').trim();
    const singer = parts[1] ? parts[1].trim() : '';
    if (title) {
      songs.push({ title, singer });
    }
  }
  
  if (songs.length === 0) {
    alert('未解析到有效歌曲');
    return;
  }
  
  appState.batchStep = 2;
  appState.batchTotal = songs.length;
  appState.batchResults = [];
  updateBatchSteps();
  
  document.getElementById('batchStep1Content').style.display = 'none';
  document.getElementById('batchStep2Content').style.display = 'block';
  document.getElementById('batchStep3Content').style.display = 'none';
  
  processBatchSongs(songs);
}

async function processBatchSongs(songs) {
  const resultList = document.getElementById('batchResultList');
  const progress = document.getElementById('batchProgress');
  
  for (let i = 0; i < songs.length; i++) {
    const song = songs[i];
    appState.batchProcessed = i + 1;
    
    progress.textContent = `已处理: ${appState.batchProcessed} / ${appState.batchTotal}`;
    
    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: song.title, singer: song.singer, source: 'gequbao' })
      });
      
      const data = await response.json();
      const candidates = data.candidates || [];
      
      if (candidates.length > 0) {
        // 获取第一个结果的夸克链接
        const first = candidates[0];
        try {
          const linkResp = await fetch('/api/get-link', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ song: first })
          });
          
          const linkData = await linkResp.json();
          if (linkData.link) {
            appState.batchResults.push({
              title: first.title,
              singer: first.singer,
              link: linkData.link,
              status: 'success'
            });
            appState.batchSuccess++;
          } else {
            appState.batchResults.push({
              title: song.title,
              status: 'failed'
            });
            appState.batchFailed++;
          }
        } catch {
          appState.batchResults.push({
            title: song.title,
            status: 'failed'
          });
          appState.batchFailed++;
        }
      } else {
        appState.batchResults.push({
          title: song.title,
          status: 'failed'
        });
        appState.batchFailed++;
      }
    } catch {
      appState.batchResults.push({
        title: song.title,
        status: 'failed'
      });
      appState.batchFailed++;
    }
    
    // 更新结果列表
    resultList.innerHTML = appState.batchResults.map(r => `
      <div class="batch-result-item ${r.status}">
        <span class="result-status">${r.status === 'success' ? '✓' : '✗'}</span>
        <span class="result-title">${r.title}</span>
      </div>
    `).join('');
    
    resultList.scrollTop = resultList.scrollHeight;
  }
  
  // 完成
  appState.batchStep = 3;
  updateBatchSteps();
  
  document.getElementById('batchStep2Content').style.display = 'none';
  document.getElementById('batchStep3Content').style.display = 'block';
  
  document.getElementById('batchSuccessCount').textContent = appState.batchSuccess;
  document.getElementById('batchFailCount').textContent = appState.batchFailed;
}

function exportBatchResults() {
  const successResults = appState.batchResults.filter(r => r.status === 'success');
  
  if (successResults.length === 0) {
    alert('没有成功的结果');
    return;
  }
  
  const content = successResults.map(r => 
    `${r.title} - ${r.singer}\n${r.link}`
  ).join('\n\n');
  
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '批量导出结果.txt';
  a.click();
  URL.revokeObjectURL(url);
}

// ============================================
// 工具函数
// ============================================

function copyLink(link) {
  if (!link) {
    alert('暂无链接');
    return;
  }
  navigator.clipboard.writeText(link).then(() => {
    alert('链接已复制');
  }).catch(() => {
    // 降级方案
    const textarea = document.createElement('textarea');
    textarea.value = link;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    alert('链接已复制');
  });
}

function openLink(link) {
  if (!link) {
    alert('暂无链接');
    return;
  }
  window.open(link, '_blank');
}

// 键盘快捷键
document.addEventListener('keydown', function(e) {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  
  switch(e.code) {
    case 'Space':
      e.preventDefault();
      togglePlay();
      break;
    case 'ArrowLeft':
      if (audio.currentTime > 5) {
        audio.currentTime -= 5;
      }
      break;
    case 'ArrowRight':
      if (audio.duration && audio.currentTime < audio.duration - 5) {
        audio.currentTime += 5;
      }
      break;
    case 'ArrowUp':
      e.preventDefault();
      volumeSlider.value = Math.min(100, parseInt(volumeSlider.value) + 5);
      audio.volume = volumeSlider.value / 100;
      break;
    case 'ArrowDown':
      e.preventDefault();
      volumeSlider.value = Math.max(0, parseInt(volumeSlider.value) - 5);
      audio.volume = volumeSlider.value / 100;
      break;
    case 'KeyM':
      toggleMute();
      break;
  }
});

// 初始化
loadFavorites();

// 暴露函数到全局作用域，供HTML onclick 调用
window.switchTab = switchTab;
window.doSearch = doSearch;
window.toggleExpandSong = toggleExpandSong;
window.playSong = playSong;
window.togglePlay = togglePlay;
window.prevSong = prevSong;
window.nextSong = nextSong;
window.toggleMute = toggleMute;
window.togglePlayerMinimize = togglePlayerMinimize;
window.toggleFavorite = toggleFavorite;
window.removeFavorite = removeFavorite;
window.exportFavorites = exportFavorites;
window.clearFavorites = clearFavorites;
window.toggleFavorites = toggleFavorites;
window.toggleBatchExport = toggleBatchExport;
window.startBatchExport = startBatchExport;
window.exportBatchResults = exportBatchResults;
window.copyLink = copyLink;
window.openLink = openLink;
window.searchRecommendSong = searchRecommendSong;
window.refreshRecommend = refreshRecommend;
window.switchPlatform = switchPlatform;
window.selectToplist = selectToplist;
window.loadApplePlaylist = loadApplePlaylist;

})();
