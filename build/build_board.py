#!/usr/bin/env python3
"""Build the Morning Market Cards board HTML for GitHub Pages.

Usage:
    build_board.py <dataset.json> <output.html> [template.html]

Dataset format:
    {"snapshot_id": N, "asOf": "2026-10-05T11:57:21.150Z",
     "asOfET": "Mon Oct 5, 2026, 7:57 AM ET (premarket)",
     "dataNotes": "...", "cards": [...]}

If template.html is omitted, uses board_template.html alongside this script.
"""
import json, sys, os, html as htmlmod
from datetime import datetime, timedelta


def format_price(card):
    price = card.get("price")
    if price is None:
        return "n/a"
    if card.get("priceUnit") == "usd_trillion":
        return f"${price:.2f}T"
    if price >= 10000:
        return f"${price:,.0f}"
    return f"${price:,.2f}"


def build_cards(cards):
    out = []
    for c in cards:
        card = {
            "symbol": c.get("symbol"),
            "label": c.get("label"),
            "category": c.get("category"),
            "priceDisplay": format_price(c),
            "changePercent": c.get("changePercent"),
            "dailyScore": c.get("dailyScore"),
            "weeklyScore": c.get("weeklyScore"),
            "monthlyScore": c.get("monthlyScore"),
            "stage": c.get("stage"),
            "stageEvidence": c.get("stageEvidence"),
            "supports": c.get("supports") or [],
            "buyZone": c.get("buyZone"),
            "invalidation": c.get("invalidation"),
            "catalyst": c.get("catalyst"),
            "price": c.get("price"),
            "pullbackStatus": c.get("pullbackStatus"),
            "riskDial": c.get("riskDial"),
        }
        if c.get("priceUnit"):
            card["priceUnit"] = c["priceUnit"]
        if c.get("dataNote"):
            card["dataNote"] = c["dataNote"]
        out.append(card)
    return out


def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print(f"usage: {sys.argv[0]} <dataset.json> <output.html> [template.html]",
              file=sys.stderr)
        sys.exit(1)

    dataset_path = sys.argv[1]
    output_path = sys.argv[2]
    if len(sys.argv) == 4:
        template_path = sys.argv[3]
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, "board_template.html")

    with open(dataset_path) as f:
        dataset = json.load(f)
    with open(template_path) as f:
        template = f.read()

    cards = build_cards(dataset.get("cards", []))
    cards_json = json.dumps(cards, separators=(",", ":"))

    # Title date: e.g. "Monday, October 5, 2026"
    # Parse from asOf (UTC ISO) and convert to America/New_York.
    # EDT (UTC-4) applies Mar–Nov; EST (UTC-5) Nov–Mar. We approximate
    # with EDT for the morning-cards use case; override via title_date
    # in the dataset if exactness matters.
    try:
        asof = datetime.fromisoformat(dataset["asOf"].replace("Z", "+00:00"))
        # Simple DST check: EDT roughly Apr–Oct
        is_dst = 4 <= asof.month <= 10
        et = asof - timedelta(hours=4 if is_dst else 5)
        title_date = et.strftime("%A, %B %-d, %Y")
    except Exception:
        title_date = dataset.get("asOfET", "")

    footer = (f"Snapshot #{dataset.get('snapshot_id')} &middot; "
              f"Data as of {htmlmod.escape(dataset.get('asOfET', ''))} &middot; "
              f"{htmlmod.escape(dataset.get('dataNotes', ''))}")

    html = template.replace("{{CARDS_JSON}}", cards_json)
    html = html.replace("{{TITLE_DATE}}", htmlmod.escape(title_date))
    html = html.replace("{{FOOTER_HTML}}", footer)

    with open(output_path, "w") as f:
        f.write(html)
    print(f"Wrote {output_path} ({len(html)} bytes, {len(cards)} cards)")


if __name__ == "__main__":
    main()
