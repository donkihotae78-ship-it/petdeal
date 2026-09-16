"""실행: python run.py [--demo] [--dry] [--site-only]
  --demo   : API 키 없이 샘플 데이터로 전체 파이프라인 검증
  --dry    : 발송 없이 콘솔 출력
  cron 예시: 0 6,12,18,0 * * * cd /srv/petdeal && python run.py >> logs/run.log 2>&1
"""
import sys
import json
import os
from datetime import datetime
from petdeal.settings import load
from petdeal.db import DB
from petdeal.collector import NaverCollector, DemoCollector
from petdeal.judge import evaluate
from petdeal.affiliate import Affiliate
from petdeal.notify import Telegram, Console, render
from petdeal.publish import build_payload, write

args = set(sys.argv[1:])
cfg = load("config.yaml")
ts = datetime.now().replace(microsecond=0).isoformat()
db = DB(os.environ.get("PD_DB", "data/petdeal.sqlite"))

use_demo = "--demo" in args or not cfg["naver"]["client_id"]
if use_demo and "--demo" not in args:
    print("[주의] NAVER_CLIENT_ID 미설정 → 데모 데이터로 실행")
    if not os.path.exists("data/sample_items.json"):
        import subprocess; subprocess.run([sys.executable, "tests/make_sample.py"], check=True)
collector = DemoCollector() if use_demo else NaverCollector(cfg["naver"])
items = collector.collect(cfg["keywords"], cfg["rules"]["min_price_krw"])
print(f"[{ts}] 수집 {len(items)}건")

deals, cat_avg = evaluate(db, items, ts, cfg["rules"])
for it in items:
    db.upsert_product(it, ts)

aff = Affiliate(cfg["affiliate"])
sender = Console() if ("--dry" in args or "--demo" in args or not cfg["telegram"]["bot_token"]) else Telegram(cfg["telegram"])
for d in deals:
    link, src = aff.convert(d)
    d["aff_link"] = link
    text = render(d, link, cfg["affiliate"]["disclosure"])
    try:
        sender.send(text)
        db.log_alert(d["product_id"], ts, d["price"], "telegram" if isinstance(sender, Telegram) else "console")
    except Exception as e:
        print("[send]", e)
db.commit()
print(f"딜 {len(deals)}건 발송")

groupbuy = json.load(open("data/groupbuy.json", encoding="utf-8")) if os.path.exists("data/groupbuy.json") else {}
channel = json.load(open("data/channel.json", encoding="utf-8")) if os.path.exists("data/channel.json") else {}
payload = build_payload(db, items, deals, cat_avg, ts, groupbuy, channel)
out = write(payload)
import shutil; os.makedirs("docs", exist_ok=True); shutil.copy(out, "docs/index.html")
print("사이트 생성:", out, "→ docs/index.html")
