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
