#!/usr/bin/env python3
"""しべの朝刊（4コマ）を公式サイト用にそろえる。

朝刊台帳.csv の「投稿済み」の行から asakan.json を作り、
まだ無い日の絵だけ asakan/<日付>.jpg（幅800・JPEG）に縮めて置く。
site_update.py が毎朝 articles.json のあとに呼ぶ。
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEDGER = Path.home() / "chie-works" / "shibe" / "notes" / "asakan" / "朝刊台帳.csv"
OUT_DIR = REPO / "asakan"
OUT_JSON = REPO / "asakan.json"


def main():
    if not LEDGER.is_file():
        print(f"ERROR: 朝刊台帳が見つかりません: {LEDGER}", file=sys.stderr)
        return 1
    with LEDGER.open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("状態") == "投稿済み"]
    rows.sort(key=lambda r: r["日付"])
    OUT_DIR.mkdir(exist_ok=True)
    items, added = [], 0
    for no, r in enumerate(rows, 1):
        day, src = r["日付"], Path(r["画像path"])
        dest = OUT_DIR / f"{day}.jpg"
        if not dest.exists():
            if not src.is_file():
                print(f"WARN: 絵が無いので飛ばします: {src}", file=sys.stderr)
                continue
            res = subprocess.run(["/usr/bin/sips", "-Z", "800", "-s", "format", "jpeg",
                                  "-s", "formatOptions", "80", str(src), "--out", str(dest)],
                                 capture_output=True, text=True, timeout=60)
            if res.returncode != 0:
                print(f"WARN: 絵の変換に失敗: {src}: {res.stderr.strip()}", file=sys.stderr)
                continue
            added += 1
        items.append({"no": no, "date": day, "title": r["タイトル"], "line": r["1文"],
                      "image": f"asakan/{day}.jpg", "url": r["URL"]})
    items.reverse()
    OUT_JSON.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"OK: 朝刊 {len(items)} 本（新しい絵 {added} 枚）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
