# yt-dl-tool

yt-dlp をベースにした動画・音声ダウンロード CLI ツールです。  
YouTube をはじめ、yt-dlp が対応するあらゆるサイトに利用できます。

## 必要環境

- Python 3.8 以上
- [FFmpeg](https://ffmpeg.org/) (音声抽出・サムネイル埋め込みに必要)

## インストール

```bash
git clone https://github.com/<あなたのユーザー名>/yt-dl-tool.git
cd yt-dl-tool
pip install -r requirements.txt
```

## 使い方

### 基本

```bash
# 最高画質で動画をダウンロード
python dl_tool.py https://www.youtube.com/watch?v=XXXXXXXXX

# 複数URLを同時指定
python dl_tool.py URL1 URL2 URL3
```

### 動画品質を指定

```bash
# 1080p
python dl_tool.py -q 1080p URL

# 720p
python dl_tool.py -q 720p URL

# 最低画質
python dl_tool.py -q worst URL
```

### 音声のみ抽出

```bash
# MP3（デフォルト）
python dl_tool.py -a URL

# FLAC（高音質）
python dl_tool.py -a --audio-format flac URL

# M4A, 320kbps
python dl_tool.py -a --audio-format m4a --audio-quality 320 URL
```

### プレイリスト

```bash
python dl_tool.py -p https://www.youtube.com/playlist?list=XXXX
```

### 動画情報・フォーマット一覧を確認

```bash
python dl_tool.py -i URL
```

### URLリストファイルから一括ダウンロード

```bash
# urls.txt に1行1URLで記述
python dl_tool.py --file urls.txt
```

### 字幕・サムネイル埋め込み

```bash
python dl_tool.py -s -t URL
```

### Cookie / プロキシ

```bash
# ブラウザから Cookie を使用（会員限定動画など）
python dl_tool.py --cookies-from-browser chrome URL

# cookies.txt を使用
python dl_tool.py --cookies /path/to/cookies.txt URL

# プロキシ経由
python dl_tool.py --proxy http://proxy.example.com:8080 URL
```

### ダウンロード速度制限

```bash
python dl_tool.py -r 1M URL    # 最大 1MB/s
python dl_tool.py -r 500K URL  # 最大 500KB/s
```

### 出力ディレクトリ変更

```bash
python dl_tool.py -o ~/Videos URL
```

## オプション一覧

| オプション | 省略形 | 説明 |
|---|---|---|
| `--output DIR` | `-o` | 出力先ディレクトリ (default: `./downloads`) |
| `--audio-only` | `-a` | 音声のみ抽出 |
| `--audio-format FMT` | | mp3 / m4a / opus / flac / wav / aac |
| `--audio-quality KBPS` | | 音声ビットレート (default: 192) |
| `--info` | `-i` | 情報のみ表示（ダウンロードしない） |
| `--quality Q` | `-q` | best / worst / 1080p / 720p 等 |
| `--format STR` | `-f` | yt-dlp フォーマット文字列を直接指定 |
| `--playlist` | `-p` | プレイリスト全体をダウンロード |
| `--subs` | `-s` | 字幕を埋め込む (ja / en) |
| `--thumbnail` | `-t` | サムネイルを埋め込む |
| `--ignore-errors` | | エラーをスキップして続行 |
| `--cookies FILE` | | cookies.txt のパス |
| `--cookies-from-browser` | | chrome / firefox / edge / safari |
| `--proxy URL` | | プロキシ URL |
| `--rate-limit` | `-r` | 速度制限 (例: 1M, 500K) |
| `--file FILE` | | URLリストファイル |

## ライセンス

MIT License
