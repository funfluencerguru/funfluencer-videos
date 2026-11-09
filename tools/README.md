# VARIETY RULE (owner request, 2026-10-24 onwards)
Do not use the same look two days in a row. Every day pick a layout + background + character set that does NOT
appear in the last 5 lines of tools/style-log.csv, then append one line to that file (date,layout,bg,chars,topic) and commit it with the video.
Layouts (--layout): single (classic, uses --prop-svg), duo, versus, chat, list, vote. Backgrounds (--bg): notebook, blackboard, sticky, graph.
Characters (--char1/--char2): boy, girl, uncle, aunty, kid. Moods (--mood1/--mood2): happy, angry, sleepy, shock.
Pick the layout that fits the joke: duo = two people arguing/joking, versus = Expectation vs Reality, chat = message screen (use generic
names like Mummy, Dost, never real apps/logos/people), list = Top 3, vote = A ya B poll. Reels stay static (no zoom).
Text for each layout goes in --data (JSON; '|' = new line inside a text):
  duo    {"a":"left speech","b":"right speech"}
  versus {"left_title":"Expectation","left_text":"..","right_title":"Reality","right_text":".."}
  chat   {"name":"Mummy","msgs":[["them","text"],["me","text"]]}   (max 4 messages, about 22 characters per line)
  list   {"title":"Top 3 ...","items":["one","two","three"]}
  vote   {"a":"Chai","b":"Coffee","hint":"Comment mein A ya B batao!"}
Example: python3 tools/make_reel.py --slug dost-late --layout duo --bg sticky --char1 boy --char2 aunty --mood2 angry \
  --data '{"a":"5 min mein aata hoon!","b":"2 ghante se yahi bol raha"}' --headline "Dost ka 5 min<br>matlab 1 ghanta" --cta "Tag karo" --date 2026-10-25 --outdir videos
Check one frame after rendering: no overlapping or cut-off text. Layouts live in tools/layouts.py.

# DAILY RULE (from 2026-10-21 onwards, set by the owner)
Every day = a NEW script AND a NEW picture. Never reuse a plain box/circle prop.
1. Pick a fresh topic/joke that is not in the last posts.
2. Draw an SVG of the main prop from that script and pass it with --prop-svg (details below).
3. Optionally change the stick figure's mood (--sleepy) and --sfx/--variant to suit the joke.
4. Check one frame: drawing must be recognisable, not overlap text or the label, nothing cut off.

# make_reel.py
Builds an 18s vertical doodle reel (1080x1920, logo bottom-right, funny synth sound).
Needs: python3, numpy, playwright (chromium), ffmpeg.

python3 tools/make_reel.py --slug chai-vs-coffee --bubble "chai ya coffee?" --prop "chai" --shape box \
  --headline "Line one<br>line two<br>line three" --cta "Comment karo" --sfx boing \
  --variant 3 --date 2026-10-18 --outdir videos

Output: videos/<date>-<slug>.mp4 -> public URL
https://raw.githubusercontent.com/funfluencerguru/funfluencer-videos/main/videos/<date>-<slug>.mp4
--sfx: beeps | growl | boing. --variant: any int (changes tune and face).

Picture must match the script: every day pass `--prop-svg <file>` with a small hand-drawn SVG of the
prop in the script (e.g. broom, chai cup, cricket bat, phone, diya). Canvas is 1000x800, right side
(x 560-960, y 380-730), plain strokes only (stroke style is inherited). Use `--prop` as its label and
`--sleepy` if it suits the joke. Behind a version mismatch set CHROMIUM_PATH=/opt/pw-browsers/chromium.
The label is drawn at (760,610): keep the drawing clear of it (draw the prop around/under it).

## Stats pillar reel (daily, `tools/make_stats_reel.py`)
Cinematic 9:16 "pillar race" stats reel: 6–10 items, lowest → highest, camera pans pillar by pillar
(bronze → silver → gold → diamond), lands with a "ka-ching", ends on an overview of all pillars + twist card.
0 ElevenLabs credits: background and icons are drawn in code, music is our own (assets/music).

    python3 tools/make_stats_reel.py spec.json                      # video + cover (+ check frames in workdir)
    python3 tools/make_stats_reel.py spec.json --preview 6.4 20     # PNG frames only (fast)

Needs python3, numpy, scipy, Pillow, ffmpeg. Renders in ~1–1.5 min. Length = 2.6 + 2×items + 6.8 s (8 items = 25.4 s).
Worked example: `tools/stats-specs/2026-11-09-price-1990-vs-2026.json` (copy it and change the text/items).

Spec fields
- `out`, `cover_out`: `videos/<date>-stats-<slug>.mp4`, `images/<date>-stats-<slug>-cover.jpg`; `workdir`: temp folder (e.g. /tmp/statsreel).
- `music`: `retro_bollywood` (nostalgia, Bollywood, India, cricket) or `future_bass` (tech, money, YouTube, modern).
- `bg`: `left_word`, `right_word` (big faded words, ≤6 chars look best), `left_color`/`right_color` [r,g,b] (mid-dark, 20–140), `motif` (one character: ₹ ★ ● ▲ ✦), `seed`.
- `intro` [big line ≤14 chars, second line ≤20 chars, small explainer]; `header` (pill shown during the first half, ≤30 chars);
  `outro` [title, subtitle]; `question` (comment bait); `twist` [bold insight ≤38 chars, small line ≤55 chars]; `sources` (one short line).
- `value_caption` (small text under each value, e.g. "TIMES COSTLIER", "CRORE PEOPLE", "RUNS"), `count_fmt` (Python format for the counting-up number, e.g. "{:,.0f}", "×{:.1f}", "₹{:,.0f} Cr"),
  `pillar_icon`: coin (money topics) | star | none.
- `cover`: `title` [3 lines], `hero` (item index for the big badge, 0-based), `pill` (hook ≤22 chars), `question` (≤14 chars).
- `items` (ordered LOW → HIGH, 6–10): `small` (top line), `big` (≤12 chars), `sub` (≤18 chars), `value` (number used for pillar height),
  `value_text` (final label, ≤7 chars), `icon`, `lines` [3 pedestal lines ≤15 chars], `vname` (vertical name in overview, ≤9 chars).
- Icons (drawn, no logos): car, post, dollar, petrol, income, silver, gold, sensex, flag, bat, trophy, phone, people, building, train, plane,
  film, food, house, bolt, or `glyph:TXT` (1–3 characters/short text, e.g. glyph:UP, glyph:4G, glyph:₹). Add new icons in `item_art()` and commit.
- Pillar height is linear from a floor, so tiny values stay visible; very skewed data (top item >30× the lowest) still works but say so in the intro line.

Rules: no photos or faces of real people, no company logos/brand artwork (names in text are fine for factual stats).
Every number must come from a source found that day; label estimates "(est.)"; write the source line. Log each reel in `tools/stats-log.csv`.
