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
