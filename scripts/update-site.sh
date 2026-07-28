#!/bin/bash
# しべ公式サイトの記事一覧を毎朝更新する（launchd: com.shibe.site-update が呼ぶ）
# SubstackのRSS → articles.json 再生成 → 変化があればコミットしてGitHub Pagesへpush。
# 認証はキーチェーンのshibe0トークンを実行時に取得（ディスクに保存しない）。
set -u
REPO="$HOME/Documents/claude-practice/shibe-site"
LOG="$REPO/scripts/site-update.log"

log() { echo "[$(date +%Y-%m-%dT%H:%M:%S)] $1" >> "$LOG"; }

cd "$REPO" || { log "ERROR: リポジトリが見つかりません"; exit 1; }

# 1. フィードを毎回取り直す（build_articles.py は /tmp/shibe-feed.xml があればそれを優先して読む）
if ! curl -sf --max-time 60 "https://shibe0.substack.com/feed" -o /tmp/shibe-feed.xml; then
  log "ERROR: フィード取得に失敗（ネットワーク?）。今日は更新スキップ"
  exit 1
fi

# 2. articles.json 再生成
if ! /usr/bin/python3 scripts/build_articles.py >> "$LOG" 2>&1; then
  log "ERROR: articles.json の生成に失敗"
  exit 1
fi

# 3. 変化がなければ何もしない（無音）
if git diff --quiet articles.json; then
  log "OK: 変化なし（新しい記事なし）"
  exit 0
fi

# 4. コミットしてpush（トークンは実行時にキーチェーンから）
git add articles.json
git commit -m "chore: 記事一覧を自動更新" >> "$LOG" 2>&1
TOKEN=$(/opt/homebrew/bin/gh auth token -u shibe0 2>/dev/null || /usr/local/bin/gh auth token -u shibe0 2>/dev/null || gh auth token -u shibe0 2>/dev/null)
if [ -z "${TOKEN:-}" ]; then
  log "ERROR: shibe0のトークンが取得できません（gh auth statusを確認）。コミットはローカルに残っています"
  exit 1
fi
if git push "https://x-access-token:${TOKEN}@github.com/shibe0/shibe0.github.io.git" main >> "$LOG" 2>&1; then
  log "OK: 新しい記事をサイトに反映しました"
else
  log "ERROR: pushに失敗。コミットはローカルに残っています"
  exit 1
fi
