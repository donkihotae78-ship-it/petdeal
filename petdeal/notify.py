"""발송: 텔레그램(즉시) / 카카오 친구톡(주간, 딜러사 API) / 콘솔(데모)"""
import requests

CAT_KO = {"dog_dry": "강아지 사료", "cat_dry": "고양이 사료", "wet": "습식·캔", "treat": "간식",
          "pad": "배변패드", "litter": "고양이 모래", "supplement": "영양제"}


def render(deal, link, disclosure):
    head = f"[{CAT_KO.get(deal['category'], deal['category'])}] {deal['title'][:60]}"
    price = f"{deal['price']:,}원"
    if deal.get("prev_min") and (deal.get("drop") or 0) > 0:
        price = f"{deal['prev_min']:,}→{deal['price']:,}원"
    lines = [head, f"💰 {price}  ({deal['mall']})"]
    for r in deal["reasons"]:
        lines.append(f"· {r}")
    if deal.get("tags"):
        lines.append("· " + " ".join(f"#{t}" for t in deal["tags"]))
    lines.append(f"구매 → {link}")
    lines.append(disclosure)
    return "\n".join(lines)


class Telegram:
    def __init__(self, cfg):
        self.url = f"https://api.telegram.org/bot{cfg['bot_token']}/sendMessage"
        self.chat = cfg["chat_id"]

    def send(self, text):
        r = requests.post(self.url, json={"chat_id": self.chat, "text": text, "disable_web_page_preview": False}, timeout=15)
        r.raise_for_status()
        return r.json()


class Console:
    def send(self, text):
        print("-" * 60)
        print(text)
        return {"ok": True}


class Kakao:
    """친구톡은 카카오 공식 딜러사(솔라피·비즈고 등) API 경유. 채널 심사·템플릿 승인 후 사용.
    여기서는 인터페이스만 고정 — provider 별 구현은 계약 후 1시간 작업."""
    def __init__(self, cfg):
        self.cfg = cfg

    def send(self, text):
        raise NotImplementedError("카카오 딜러사 계약 후 provider 구현 필요 (config.kakao.provider)")
