# Morning Market Cards

A daily market snapshot board — one card per ticker with price, trend scores,
Weinstein stage, supports, buy zones, and invalidation levels.

**Live board:** https://avkashc.github.io/morning-stocks-cards/

## How it works

```
8:00 AM ET  Market data refresh (Finnhub for equities, CoinGecko for crypto)
            → 21-card snapshot with scores, stages, EMAs, supports
8:10 AM ET  Dataset JSON built from the snapshot
            → build/build_board.py renders index.html from build/board_template.html
            → build/update_board.sh commits & pushes (skips if unchanged)
            → GitHub Pages serves the update within a minute or two
            → Morning email sent with the board link
```

## Repository layout

| Path | Purpose |
|---|---|
| `index.html` | The built board, served by GitHub Pages. Regenerated daily — do not edit by hand. |
| `.nojekyll` | Tells Pages to serve files directly without Jekyll processing. |
| `build/board_template.html` | HTML/CSS/JS template. Placeholders: `{{CARDS_JSON}}`, `{{TITLE_DATE}}`, `{{FOOTER_HTML}}`. Edit this to change the dashboard design. |
| `build/build_board.py` | Renders the template with a dataset JSON. Usage: `build_board.py <dataset.json> <output.html> [template.html]` |
| `build/update_board.sh` | Builds + commits + pushes. Usage: `update_board.sh <dataset.json> [repo-dir]`. Skips the push when nothing changed. |

## Making dashboard improvements

Edit `build/board_template.html` (styling, layout, controls) or
`build/build_board.py` (data shaping) and commit. The next daily run picks up
your changes automatically because the pipeline builds from this repo's scripts.

To preview locally before the daily run:

```bash
python3 build/build_board.py path/to/dataset.json /tmp/preview.html
open /tmp/preview.html   # or: python3 -m http.server --directory /tmp
```

Dataset format:

```json
{
  "snapshot_id": 28,
  "asOf": "2026-10-05T11:57:21.150Z",
  "asOfET": "Mon Oct 5, 2026, 7:57 AM ET (premarket)",
  "dataNotes": "Equities are Friday's closes; crypto is live (24h basis).",
  "cards": [
    {
      "symbol": "SPY", "label": "S&P 500 ETF", "category": "Market",
      "price": 769.64, "changePercent": 0.74,
      "dailyScore": 7, "weeklyScore": 8, "monthlyScore": 10,
      "stage": "Stage 2", "stageEvidence": "...",
      "supports": [{"level": "$754.05", "rating": 6}],
      "buyZone": "...", "invalidation": "...", "catalyst": "...",
      "pullbackStatus": "No active pullback", "riskDial": "Focus"
    }
  ]
}
```

## Data pipeline

Live market data, trend-score computation, and stage classification run in the
`morning-market-cards` web app (8:00 AM ET refresh). This repo owns the
presentation layer: template, rendering, and publishing. The daily pipeline that
feeds this repo is unchanged.
