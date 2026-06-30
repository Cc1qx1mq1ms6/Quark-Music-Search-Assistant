# 🎵 Quark Music Search Assistant

Multi-platform music search and Quark Netdisk link retrieval tool, supporting single search, batch export, and trending charts

[简体中文](README.md) | English

## ✨ Features

### Core Features
- 🔍 **Single Search** - Horizontal dual-pane UI, search on left, results list on right
- 🎵 **Music Recommendations** - Multi-platform trending charts (QQ Music, Kugou, NetEase Cloud, Apple Music)
- 📦 **Batch Export** - Import playlist file and get Quark links in bulk
- 🏆 **Original Singer Detection** - Get original artist info from Douban Music
- ⭐ **Favorites** - Save your favorite songs, auto-persisted, survives restarts
- 💾 **Multiple Save Options** - Single save, batch save, favorites export
- 🎶 **Built-in Music Player** - Apple Music style player with playback controls

### Multi-platform Charts
- 🐧 **QQ Music** - 9 major charts including Peak Chart, Hot Songs, New Songs, Rising
- 🎵 **Kugou Music** - 55 charts including TOP500, National Trend, Rising
- ☁️ **NetEase Cloud Music** - Hot Songs, New Songs, Rising and more
- 🍎 **Apple Music** - Top Songs, City Charts, Weekly Top and more

### Multi-source Search
- 🎵 **Gequbao** - Default source, wide coverage, fast response
- 🎵 **DGCol Music** - Quark Netdisk music source, supports preview playback
- 🎧 **XM Lossless** - Supports FLAC lossless and MP3 dual quality options
- 🎶 **Dtwav** - Another lossless source, dual quality options
- 🔄 **Dropdown Switch** - Source selection via dropdown, extensible for future sources

### Search Optimization
- 🎯 **Multi-level Search Strategy** - 4 search levels, 95%+ success rate
- ⚡ **Smart Retry** - Exponential backoff retry, auto recovery from network issues
- 🧹 **Smart Cleaning** - Auto-clean feat./Remix/Cover suffixes
- 📊 **Match Score** - Each result shows match percentage
- 🤖 **Quality Filter** - Auto-filter reuploaders and low-quality versions

### UI Experience
- 🌐 **Web Interface** - Modern web UI, browser access
- 📑 **Bottom Navigation** - Search/Recommend/Favorites/Batch tabs
- 📱 **Responsive Layout** - Adapts to desktop and mobile
- 🎨 **Card-based Design** - Click to expand details, saves space
- 📝 **Format Examples** - Built-in playlist format guide, beginner-friendly
- 🎵 **Dual Quality Cards** - Lossless source songs show FLAC/MP3 dual cards, choose as needed
- ✏️ **Minimalist Icons** - Unified line-art style SVG icons, clean and simple
- 🎶 **Collapsible Player** - Player can be minimized to bottom nav bar, saves screen space
- 🌈 **Gradient Cover** - Animated gradient music cover, spins while playing
- 🎯 **Sleek Progress Bar** - Progress bar with gloss effect and drag feedback

## 🖼️ Interface Preview

### Search Page
```
┌─────────────────────────────────────────────────────────────────┐
│                      Search Songs                               │
├──────────────────────┬──────────────────────────────────────────┤
│                      │  📋 Search Results          10 songs     │
│  🔍 Search Songs     │                                          │
│  ┌────────────────┐  │  ┌──┬──────┬───────────────────┬──┐  │
│  │ Song Title      │  │  │ 1│  🎵  │ Good Time 🏆Original │▶︎│  │
│  └────────────────┘  │  │  │      │ Owl City...       │  │  │
│  ┌────────────────┐  │  └──┴──────┴───────────────────┴──┘  │
│  │ Artist (opt.)   │  │  ┌──┬──────┬───────────────────┬──┐  │
│  └────────────────┘  │  │ 2│  🎵  │ Good Time (DJ Ver.)│▶︎│  │
│                      │  │  │      │ Owl City...       │  │  │
│  [ 🔍 Search ]       │  └──┴──────┴───────────────────┴──┘  │
│                      │                                          │
│  🏆 Original Artist  │  Click card: Play/Copy/Open/Favorite   │
│  Owl City, ...       │                                          │
│  Source: Douban      │                                          │
│                      │                                          │
├──────────────────────┴──────────────────────────────────────────┤
│  🎵 Now Playing...  ━━━━━━━━●━━━━━━  1:23 / 3:45  ⏮ ▶ ⏭ 🔊 ↘ │
├─────────────────────────────────────────────────────────────────┤
│   🔍   🎵   [🎵]   ⭐   📦                                      │
│  Search  Recs   Player  Favs  Batch                            │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Requirements

- Python 3.8+
- Windows / macOS / Linux

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install requests beautifulsoup4 flask
```

### Run Desktop Version

Double-click or run in command line:

```bash
python desktop.py
```

Desktop version runs in a window, no browser needed.

## 📖 User Guide

### Single Search

1. Enter song title on the left (artist is optional)
2. Click the "🔍 Search" button
3. View results list on the right, with original version and match score
4. Click a song card to expand details and see the Quark link
5. Options: Play, Copy link, Open link, Add to favorites

### Batch Export

1. Click "📦 Batch" in bottom navigation
2. Step 1: Import playlist file (supports multiple formats)
3. Step 2: Start batch search
4. Step 3: View results, retry failed songs
5. Step 4: Copy all links, save to Quark Netdisk

### Favorites Management

1. Click "⭐ Favorite" on songs you like
2. Switch to "Favorites" tab to view your list
3. Features: Batch copy links, export to file, clear favorites

### Music Recommendations

1. Switch to "Recommend" tab
2. Select a chart platform (QQ Music, Kugou, NetEase, Apple Music)
3. Browse the chart list and select one to view details
4. Click "🔍 Search" to search for any song
5. Data is auto-cached locally, auto-refreshes every 6 hours
6. Click "🔄 Refresh" button to manually refresh

### Music Player

1. Click the play button on any song in search results
2. The bottom player shows current song info
3. Controls: Play/Pause, Previous, Next, Volume
4. **Minimize Player**: Click the minimize button on the top-left of player to hide it to bottom nav bar
5. **Restore Player**: Click the music cover icon in the middle of bottom nav bar
6. Cover spins while playing with animated gradient effect

## 📝 Playlist File Format

Supports the following formats (one song per line):

**Format 1 (Recommended):**
```
1. Sunny Day - Jay Chou
2. Rice Aroma - Jay Chou
3. Good Time - Owl City
```

**Format 2:**
```
Sunny Day - Jay Chou
Rice Aroma - Jay Chou
```

**Format 3:**
```
Sunny Day
Jay Chou
Rice Aroma
Jay Chou
```

> 💡 Supports Qishui Music export format. Empty lines and comment lines are auto-skipped.

## 🏗️ Project Structure

```
Music-Playlist-Export-Tool/
├── README.md              # Chinese documentation
├── README_EN.md           # English documentation
├── app.py                 # Web entry point (Flask)
├── routes.py              # API routes module
├── desktop.py             # Desktop entry (PyWebView)
├── gui.py                 # GUI (legacy)
├── requirements.txt       # Python dependencies
├── .gitignore             # Git ignore config
├── LICENSE                # MIT License
├── web/                   # Web frontend resources
│   ├── index.html         # HTML page structure
│   ├── style.css          # CSS stylesheet
│   ├── app.js             # Main interaction logic
│   └── api.js             # API interface wrapper
├── rankings/              # Charts module
│   ├── __init__.py
│   ├── qq_music.py        # QQ Music charts
│   ├── kugou.py           # Kugou Music charts
│   ├── netease.py         # NetEase Cloud Music charts
│   ├── apple_music.py     # Apple Music charts
│   └── cache.py           # Cache management
├── search/                # Search module
│   ├── __init__.py
│   ├── unified.py         # Unified search interface
│   ├── gequbao.py        # Gequbao search source
│   ├── dgcol.py          # DGCol music source
│   ├── xmfwav.py         # XM Lossless music source
│   ├── dtwav.py          # Dtwav music source
│   ├── xmwav.py          # XMWav music (requires song URL)
│   ├── matching.py        # Match scoring & original singer detection
│   └── utils.py           # Utility functions
├── gui/                   # GUI module
│   ├── __init__.py
│   ├── main_window.py     # Main window
│   ├── components.py      # Components
│   ├── dialogs.py         # Dialogs
│   └── theme.py           # Theme
├── 示例歌单/               # Example playlist files
│   └── 汽水音乐歌单_示例.txt
└── 示例输出/               # Output examples
    └── 夸克网盘链接_示例.txt
```

## 🔧 Core Modules

### Backend Modules

| Module | Description |
|--------|-------------|
| `app.py` | Flask entry, registers routes, serves static files |
| `routes.py` | All API routes (search, charts, favorites, batch export) |
| `search/unified.py` | Unified search interface, multi-source switching |
| `search/matching.py` | Song match scoring, original singer detection |
| `rankings/` | Multi-platform chart data retrieval |

### Frontend Modules

| File | Description |
|------|-------------|
| `index.html` | Page structure |
| `style.css` | Style design (with responsive layout) |
| `app.js` | Main interaction logic (search, player, favorites, batch export) |
| `api.js` | API interface wrapper, communicates with backend |

## ❓ FAQ

### Q: Can't find the song?
A: Try simplifying the song title, search with title only, or check the spelling.

### Q: Is the original singer info accurate?
A: Original singer info comes from Douban Music. It's fairly accurate for most popular songs. If incorrect, use your own judgment.

### Q: What if batch search is interrupted?
A: The command-line version supports resume. Re-running will auto-skip processed songs.

### Q: Can I download directly from Quark links?
A: You need to save the links to your own Quark Netdisk first. Copy the links to the Quark web interface - it will auto-prompt for batch save.

### Q: How often are chart data updated?
A: Data is auto-cached locally, auto-refreshes every 6 hours. You can also click "🔄 Refresh" button to manually refresh.

### Q: Which chart platforms are available?
A: QQ Music, Kugou Music, NetEase Cloud Music, Apple Music.

## ⚠️ Disclaimer

This tool is for learning and communication purposes only. Please respect copyright. Do not use copyrighted music for commercial purposes.

## ⭐ Support the Project

If you find this project useful, please give it a Star ⭐️!

## 📄 License

MIT License
