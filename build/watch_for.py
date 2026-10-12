#!/usr/bin/env python3
"""Generate the per-card "Watch for" trigger line for Morning Market Cards.

One line per card, plain language, with a specific price level: the condition
that would make the ticker worth opening. Derived only from fields the cards
already carry (price, stage, supports, buyZone, invalidation, pullbackStatus,
scores) — no new data pipeline.

Rules (first match wins):
  1. Healthy pullback -> tag-of-support trigger
  2. Stage 4 -> reclaim-of-trend trigger
  3. Stage 3 -> 4 -> reclaim-to-negate trigger
  4. Extended Stage 2 (hot daily, far from support) -> wait-for-pullback
  5. Price below nearest support -> reclaim trigger
  6. Near support (<=3% above) -> hold-and-bounce trigger
  7. Stage 2 -> 3 -> resolution trigger at invalidation
  8. Stage 1 -> 2 -> breakout-watch trigger
  9. Mixed/unconfirmed pullback -> wait-for-clarity
  10. Fallback -> buy zone, then invalidation

Not a score, not a signal. Never padded with vague lines.
"""
import re


def _parse_level(s):
    """Extract a numeric price from strings like '$754.05' or 'Near $754.05...'."""
    if not s:
        return None
    m = re.search(r"[\d,]+\.?\d*", str(s).replace("$", ""))
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def _fmt(v):
    return f"${v:,.2f}"


def build_watch_for(c):
    price = c.get("price")
    stage = c.get("stage") or ""
    supports = c.get("supports") or []
    buy_zone = c.get("buyZone")
    invalidation = c.get("invalidation")
    pullback = c.get("pullbackStatus")
    daily = c.get("dailyScore")

    nearest = None
    if supports:
        s0 = supports[0]
        val = _parse_level(s0.get("level"))
        nearest = {
            "level": s0.get("level"),
            "value": val,
            "rating": s0.get("rating"),
        }

    dist_pct = None
    if price and nearest and nearest["value"]:
        dist_pct = (price - nearest["value"]) / price * 100

    def sup_label():
        lvl = nearest["level"] if nearest else None
        rating = nearest.get("rating") if nearest else None
        if lvl and rating is not None:
            return f"{lvl} ({rating}/10)"
        return lvl or "support"

    # 1. Healthy pullback in progress -> the tag is the trigger
    if pullback == "Healthy pullback" and nearest and nearest["level"]:
        return (
            f"Tag of {sup_label()} on quiet volume — "
            f"pullback entry candidate on a hold with drying volume."
        )

    # 2. Stage 4 -> only a reclaim matters
    if stage == "Stage 4":
        return "Base forming and a reclaim of the 30-week trend — no longs until then."

    # 3. Stage 3 -> 4 -> reclaim negates, otherwise dead money
    if stage == "Stage 3 → 4":
        return "Reclaim of the 30-week trend to negate the breakdown; otherwise dead money."

    # 4. Extended Stage 2 -> wait for the pullback, don't chase
    if (
        stage == "Stage 2"
        and daily is not None
        and daily >= 8
        and dist_pct is not None
        and dist_pct > 5
        and nearest
        and nearest["level"]
    ):
        return (
            f"Pullback toward {sup_label()}; "
            f"extended {dist_pct:.0f}% above support — don't chase."
        )

    # 5. Below nearest support -> needs to reclaim it
    if dist_pct is not None and dist_pct < -1 and nearest and nearest["level"]:
        return (
            f"Reclaim of {sup_label()} — "
            f"back below support, wait for repair before any entry."
        )

    # 6. Near support -> hold-and-bounce is the trigger
    if dist_pct is not None and -1 <= dist_pct <= 3 and nearest and nearest["level"]:
        return (
            f"Hold of {sup_label()} — "
            f"a bounce with volume turns this into a pullback entry."
        )

    # 7. Stage 2 -> 3 -> resolution at the invalidation level
    if stage == "Stage 2 → 3":
        lvl = _parse_level(invalidation)
        lvl_s = _fmt(lvl) if lvl else "support"
        return (
            f"Resolution at {lvl_s} — a hold stabilizes the topping pattern, "
            f"a daily close below confirms it."
        )

    # 8. Stage 1 -> 2 -> breakout watch
    if stage == "Stage 1 → 2":
        return "Volume-backed follow-through — breakout watch, check volume on the reclaim."

    # 9. Mixed signals -> wait for clarity
    if pullback == "Mixed/unconfirmed pullback":
        return "Volume and range resolving in one direction — no entry on mixed signals."

    # 10. Fallback: buy zone, then invalidation
    if buy_zone:
        return f"Price reaching the buy zone ({buy_zone})."
    if invalidation:
        return f"Reaction at invalidation ({invalidation})."
    return None
