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
from datetime import datetime
from zoneinfo import ZoneInfo


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
        card = dict(c)
        card.update({
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
        })
        scores = c.get("score_breakdown") or {}
        for horizon in ("daily", "weekly", "monthly"):
            if horizon in scores:
                card[horizon + "Score"] = scores[horizon].get("value")
        if "stage_detail" in c:
            detail = c.get("stage_detail") or {}
            card["stage"] = detail.get("stage")
            card["stageEvidence"] = detail.get("evidence")
        if "pullback_detail" in c:
            card["pullbackStatus"] = (c.get("pullback_detail") or {}).get("status")
        if "risk_detail" in c:
            card["riskDial"] = (c.get("risk_detail") or {}).get("dial")
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

    asof_text = dataset.get("snapshot_utc") or dataset.get("asOf")
    display_time = dataset.get("snapshot_et") or dataset.get("asOfET") or asof_text or "Timestamp unavailable"
    try:
        asof = datetime.fromisoformat(asof_text.replace("Z", "+00:00"))
        et = asof.astimezone(ZoneInfo("America/New_York"))
        title_date = et.strftime("%A, %B %d, %Y")
    except (ValueError, TypeError, AttributeError):
        title_date = display_time
    notes = dataset.get("dataNotes") or "Quote and analytical times are shown per card; trend scores describe price history."
    versions = dataset.get("methodology_versions") or {}
    footer = (f"Snapshot #{dataset.get('snapshot_id')} &middot; "
              f"{htmlmod.escape(display_time)} &middot; "
              f"{htmlmod.escape(notes)}")
    if versions:
        footer += "<br>" + htmlmod.escape(" · ".join(f"{k} {v}" for k, v in versions.items()))
    # Prevent dataset text from terminating the inline script element.
    cards_json = cards_json.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

    briefing_json = json.dumps(dataset.get("snapshot_comparison") or dataset.get("daily_briefing") or {}, separators=(",", ":"))
    briefing_json = briefing_json.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    market_json = json.dumps(dataset.get("market_context") or {}, separators=(",", ":"))
    market_json = market_json.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    html = template.replace("{{CARDS_JSON}}", cards_json).replace("{{BRIEFING_JSON}}", briefing_json).replace("{{MARKET_CONTEXT_JSON}}", market_json)
    html = html.replace("{{TITLE_DATE}}", htmlmod.escape(title_date))
    html = html.replace("{{FOOTER_HTML}}", footer)
    html = html.replace("{{ASOF_ET}}", htmlmod.escape(display_time))
    html = html.replace("{{DATA_NOTES}}", htmlmod.escape(notes))

    with open(output_path, "w") as f:
        f.write(html)
    print(f"Wrote {output_path} ({len(html)} bytes, {len(cards)} cards)")


if __name__ == "__main__":
    main()




