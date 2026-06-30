const API = {
  async search(title, singer = '', source = 'gequbao') {
    const res = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, singer, source })
    });
    return res.json();
  },

  async getLink(song) {
    const res = await fetch('/api/get-link', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ song })
    });
    return res.json();
  },

  async getPlayUrl(song) {
    const res = await fetch('/api/play', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ song })
    });
    return res.json();
  },

  async getToplists(platform = 'qq') {
    const res = await fetch(`/api/toplists?platform=${encodeURIComponent(platform)}`);
    return res.json();
  },

  async getToplistDetail(platform, id) {
    const res = await fetch(`/api/toplist-detail?platform=${encodeURIComponent(platform)}&id=${encodeURIComponent(id)}`);
    return res.json();
  },

  async getPlaylistCategories() {
    const res = await fetch('/api/playlist-categories');
    return res.json();
  },

  async getPlaylists(category) {
    const res = await fetch(`/api/playlists?cat=${encodeURIComponent(category)}`);
    return res.json();
  },

  async searchRecommendSong(title, singer, source = 'gequbao') {
    const res = await fetch('/api/search-recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, singer, source })
    });
    return res.json();
  },

  async batchExport(songs, source = 'gequbao') {
    const res = await fetch('/api/batch-export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ songs, source })
    });
    return res.json();
  }
};
