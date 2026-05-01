#!/usr/bin/env python3
"""
yt-dl-tool: YouTube / 各種サイト対応ダウンロードツール (yt-dlp ベース)
"""

import argparse
import sys
import os
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("[ERROR] yt-dlp が見つかりません。`pip install yt-dlp` を実行してください。")
    sys.exit(1)


# ─────────────────────────────────────────────
#  進捗フック
# ─────────────────────────────────────────────
class ProgressHook:
    def __init__(self):
        self._prev_percent = -1

    def __call__(self, d: dict):
        status = d.get("status")

        if status == "downloading":
            total   = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            current = d.get("downloaded_bytes", 0)
            speed   = d.get("speed") or 0
            eta     = d.get("eta") or 0

            if total:
                percent = int(current / total * 100)
                if percent != self._prev_percent:
                    bar = "█" * (percent // 5) + "░" * (20 - percent // 5)
                    speed_str = _fmt_size(speed) + "/s" if speed else "---"
                    eta_str   = f"{eta}s" if eta else "---"
                    print(
                        f"\r  [{bar}] {percent:3d}%  {_fmt_size(current)}/{_fmt_size(total)}"
                        f"  速度:{speed_str}  残り:{eta_str}   ",
                        end="", flush=True,
                    )
                    self._prev_percent = percent
            else:
                downloaded_str = _fmt_size(current)
                print(f"\r  ダウンロード中... {downloaded_str}", end="", flush=True)

        elif status == "finished":
            print(f"\n  ✔ ダウンロード完了: {d.get('filename', '')}")

        elif status == "error":
            print(f"\n  ✘ エラー発生")


def _fmt_size(size_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


# ─────────────────────────────────────────────
#  オプション構築
# ─────────────────────────────────────────────
def build_ydl_opts(args: argparse.Namespace) -> dict:
    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    outtmpl = str(output_dir / "%(title)s.%(ext)s")
    if args.playlist:
        outtmpl = str(output_dir / "%(playlist_index)02d - %(title)s.%(ext)s")

    opts: dict = {
        "outtmpl"             : outtmpl,
        "progress_hooks"      : [ProgressHook()],
        "ignoreerrors"        : args.ignore_errors,
        "noplaylist"          : not args.playlist,
        "writesubtitles"      : args.subs,
        "writeautomaticsub"   : args.subs,
        "subtitleslangs"      : ["ja", "en"] if args.subs else [],
        "embedsubtitles"      : args.subs,
        "embedthumbnail"      : args.thumbnail,
        "addmetadata"         : True,
        "quiet"               : False,
        "no_warnings"         : False,
        "nocheckcertificate"  : args.no_check_certificate,
    }

    # ── 音声のみ ──
    if args.audio_only:
        opts["format"] = "bestaudio/best"
        fmt = args.audio_format.lower()
        opts["postprocessors"] = [
            {
                "key"            : "FFmpegExtractAudio",
                "preferredcodec" : fmt,
                "preferredquality": args.audio_quality,
            },
            {"key": "FFmpegMetadata"},
        ]
        if args.thumbnail:
            opts["postprocessors"].append({"key": "EmbedThumbnail"})

    # ── 動画 ──
    else:
        if args.format:
            opts["format"] = args.format
        elif args.quality == "best":
            opts["format"] = "bestvideo+bestaudio/best"
        elif args.quality == "worst":
            opts["format"] = "worstvideo+worstaudio/worst"
        else:
            height = args.quality.rstrip("p")
            opts["format"] = (
                f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
            )

        pp = [{"key": "FFmpegMetadata"}]
        if args.thumbnail:
            pp.append({"key": "EmbedThumbnail"})
        opts["postprocessors"] = pp

    # ── cookies / proxy ──
    if args.cookies:
        opts["cookiefile"] = args.cookies
    if args.cookies_from_browser:
        opts["cookiesfrombrowser"] = (args.cookies_from_browser,)
    if args.proxy:
        opts["proxy"] = args.proxy

    # ── レート制限 ──
    if args.rate_limit:
        opts["ratelimit"] = _parse_rate(args.rate_limit)

    return opts


def _parse_rate(rate_str: str) -> int:
    """例: '1M' -> 1048576, '500K' -> 512000"""
    rate_str = rate_str.strip().upper()
    if rate_str.endswith("K"):
        return int(float(rate_str[:-1]) * 1024)
    elif rate_str.endswith("M"):
        return int(float(rate_str[:-1]) * 1024 * 1024)
    return int(rate_str)


# ─────────────────────────────────────────────
#  情報取得
# ─────────────────────────────────────────────
def show_info(url: str, no_check_cert: bool = False):
    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "nocheckcertificate": no_check_cert}) as ydl:
        info = ydl.extract_info(url, download=False)

    print(f"\n{'─'*50}")
    print(f"  タイトル  : {info.get('title', 'N/A')}")
    print(f"  投稿者    : {info.get('uploader', 'N/A')}")
    print(f"  時間      : {_fmt_duration(info.get('duration', 0))}")
    print(f"  視聴数    : {info.get('view_count', 'N/A'):,}" if isinstance(info.get('view_count'), int) else f"  視聴数    : {info.get('view_count', 'N/A')}")
    print(f"  URL       : {info.get('webpage_url', url)}")
    print(f"{'─'*50}")

    formats = info.get("formats", [])
    if formats:
        print("\n  利用可能フォーマット (抜粋):")
        print(f"  {'ID':<12} {'拡張子':<8} {'解像度':<12} {'コーデック':<20} {'サイズ'}")
        print(f"  {'─'*12} {'─'*8} {'─'*12} {'─'*20} {'─'*10}")
        for f in formats[-20:]:
            fid   = f.get("format_id", "")
            ext   = f.get("ext", "")
            res   = f.get("resolution") or f"{f.get('width','?')}x{f.get('height','?')}"
            vcodec = f.get("vcodec", "")
            acodec = f.get("acodec", "")
            codec = f"{vcodec}/{acodec}"
            fsize = _fmt_size(f.get("filesize") or f.get("filesize_approx") or 0)
            print(f"  {fid:<12} {ext:<8} {res:<12} {codec:<20} {fsize}")


def _fmt_duration(sec: int) -> str:
    if not sec:
        return "N/A"
    h, r = divmod(int(sec), 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


# ─────────────────────────────────────────────
#  メイン
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="dl_tool",
        description="yt-dlp ベースの動画・音声ダウンロードツール",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("urls", nargs="*", help="ダウンロードするURL（複数指定可）")
    parser.add_argument("-f", "--file",  help="URLリストファイル（1行1URL）")
    parser.add_argument("-o", "--output", default="./downloads", help="出力ディレクトリ (default: ./downloads)")

    # ── モード ──
    mode = parser.add_argument_group("モード")
    mode.add_argument("-a", "--audio-only",    action="store_true", help="音声のみ抽出")
    mode.add_argument("--audio-format",        default="mp3",
                      choices=["mp3", "m4a", "opus", "flac", "wav", "aac"],
                      help="音声フォーマット (default: mp3)")
    mode.add_argument("--audio-quality",       default="192",
                      help="音声ビットレート kbps (default: 192)")
    mode.add_argument("-i", "--info",          action="store_true", help="動画情報・フォーマット一覧を表示してダウンロードしない")

    # ── 品質 ──
    quality = parser.add_argument_group("品質")
    quality.add_argument("-q", "--quality",   default="best",
                         help="動画品質: best / worst / 1080p / 720p / 480p / 360p (default: best)")
    quality.add_argument("--format",          help="yt-dlp フォーマット文字列を直接指定 (-q より優先)")

    # ── オプション ──
    opts = parser.add_argument_group("オプション")
    opts.add_argument("-p", "--playlist",            action="store_true", help="プレイリスト全体をダウンロード")
    opts.add_argument("-s", "--subs",                action="store_true", help="字幕を埋め込む (ja / en)")
    opts.add_argument("-t", "--thumbnail",           action="store_true", help="サムネイルを埋め込む")
    opts.add_argument("--ignore-errors",             action="store_true", help="エラーをスキップして続行")
    opts.add_argument("--no-check-certificate",      action="store_true", help="SSL証明書の検証をスキップ")
    opts.add_argument("--cookies",                   help="cookies.txt のパス")
    opts.add_argument("--cookies-from-browser",
                      choices=["chrome", "firefox", "edge", "safari"],
                      help="ブラウザから Cookie を読み込む")
    opts.add_argument("--proxy",                     help="プロキシ URL (例: http://proxy:8080)")
    opts.add_argument("-r", "--rate-limit",          help="ダウンロード速度制限 (例: 1M, 500K)")

    args = parser.parse_args()

    # URL 収集
    urls = list(args.urls)
    if args.file:
        fpath = Path(args.file)
        if not fpath.exists():
            print(f"[ERROR] ファイルが見つかりません: {fpath}")
            sys.exit(1)
        lines = [l.strip() for l in fpath.read_text().splitlines() if l.strip() and not l.startswith("#")]
        urls.extend(lines)

    if not urls:
        parser.print_help()
        sys.exit(0)

    print(f"\n  yt-dl-tool  |  {len(urls)} 件のURLを処理します\n")

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")

        if args.info:
            show_info(url, no_check_cert=args.no_check_certificate)
            continue

        ydl_opts = build_ydl_opts(args)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except yt_dlp.utils.DownloadError as e:
            print(f"  [ERROR] {e}")
            if not args.ignore_errors:
                sys.exit(1)

    print("\n  ✅ 全処理完了")


if __name__ == "__main__":
    main()
