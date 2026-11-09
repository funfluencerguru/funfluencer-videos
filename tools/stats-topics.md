# Daily stats reel: topic plan (owner topics first, updated 2026-11-09)

How a daily run uses this file:
- Take the FIRST topic below whose slug is not already in `tools/stats-log.csv`.
- Exception: if something big is trending in India today and fits a stats reel (match result, record, festival sale, budget), you may do that instead. Log it and leave the planned topic for the next day.
- Never use the same category two days in a row (check the last line of the log). If needed, skip to the next topic with a different category.
- Circle icons: India topics use the illustrated India icon pack (img:NAME, see tools/README.md); cricket/world topics use drawn flags (flag:CODE) for players, teams and countries. No photos or faces, no logos. Names of public figures or film titles in text are fine.
- Every number must come from sources found that day. If good data can't be found, skip to the next topic.
- THEME: set the spec `theme` from the category: cricket -> cricket; sports -> sports; bollywood-box-office -> bollywood; money-then-vs-now, money-india, money-world -> money; youtube-internet -> tech; science-fun, world-records -> space (or geo for nature/mountains/rivers); india-states, india-geo -> geo; india-cities -> city; world-vs-india -> world. social-media, youtube-internet, gaming -> tech; bollywood-stars -> bollywood; history -> world. The theme brings the matching background and music.
- Owner's topic list (added 2026-11-09) is at the top in priority order. Owner rule: ranking lists are always the TOP 10 only (10 pillars, shown #10 up to #1), never top 50 or top 100.
- Owner-approved: neutral history topics such as PM tenure are allowed (numbers and names only, no party names, no opinions). Tragedies and disasters are never stats-reel topics.
- REAL-PHOTO BADGES (owner wants real-looking pictures wherever possible): if assets/icons has a `ph_<name>.png` badge for an item, use it (`img:ph_<name>`) instead of the drawn icon. Available now: Indian states (ph_uttarpradesh, ph_maharashtra, ph_bihar, ph_westbengal, ph_madhyapradesh, ph_tamilnadu, ph_rajasthan, ph_karnataka, ph_gujarat, ph_andhrapradesh, ph_odisha, ph_telangana, ph_kerala, ph_chhattisgarh, ph_delhi, ph_himachal, ph_goa, ph_mizoram). For a state with no ph_ badge, use the illustrated pack icon. See tools/real-photo-sheets.md.
- YouTube channels, games and brands: no logos; use glyph:XX initials (or a flag for a person's country).
- When the list runs out, add 30 new topics in the same style (same categories, new ideas) and commit the file.

| # | slug | category | topic (low to high, 6-10 items) | theme (background + music) |
|---|------|----------|---------------------------------|-------|
| 0 | odi-most-centuries | cricket | Most ODI centuries (all-time) — DONE 2026-11-10 | cricket |
| 1 | ronaldo-fastest-1m-subs | youtube-internet | Fastest YouTube channels to 1 million subscribers (hours/days; Cristiano Ronaldo's UR channel at the top). Icons: glyph initials, no logos | tech |
| 2 | richest-ipl-players | cricket | Top 10: Highest-paid IPL players, latest season (₹ crore per season). Flags for players | cricket |
| 3 | gold-price-1950-2026 | money-then-vs-now | Gold price per 10 g in India, 1950 to 2026 (one pillar per decade + 2026) | money |
| 4 | most-followed-instagram-world | social-media | Top 10: Most-followed Instagram accounts in the world (crore followers). Flags for people, glyph for brands | tech |
| 5 | most-expensive-weddings | money-world | Most expensive weddings ever (est. cost ₹ crore; Ambani wedding at the top). Label all costs (est.) | money |
| 6 | cricket-jersey-numbers | cricket | Famous jersey numbers of cricket legends (pillar = the number, low to high; name + fun fact on pedestal). Flags | cricket |
| 7 | most-subscribed-youtube-world | youtube-internet | Top 10: Most-subscribed YouTube channels in the world (crore subscribers). Glyph initials, no logos | tech |
| 8 | richest-indians-2026 | money-india | Top 10: Richest Indians, latest list (net worth $ billion / ₹ lakh crore) | money |
| 9 | indian-actresses-instagram | bollywood-stars | Top 10: Most-followed Indian actresses on Instagram (crore followers). Glyph initials, no photos | bollywood |
| 10 | most-played-games | gaming | Top 10: Most-played video games right now (monthly players, crore). Glyph initials, no logos | tech |
| 11 | cricketers-instagram-followers | cricket | Top 10: Cricketers with the most Instagram followers (crore). Flags | cricket |
| 12 | years-since-independence | history | How old is your country? Years since independence: India vs other countries (flags) | world |
| 13 | fastest-to-100m-subs | youtube-internet | Fastest YouTube channels to 100 million subscribers (years). Glyph initials | tech |
| 14 | bollywood-top-grossers-2025 | bollywood-box-office | Highest-grossing Hindi films of 2025 (₹ crore worldwide) | bollywood |
| 15 | indian-gaming-channels | gaming | Top 10: Most-subscribed Indian gaming YouTube channels (lakh subscribers). Glyph initials | tech |
| 16 | most-followed-indians-instagram | social-media | Top 10: Most-followed Indians on Instagram (crore followers). Glyph initials | tech |
| 17 | longest-serving-indian-pms | history | Longest-serving Prime Ministers of India (years in office). Neutral facts only: names + years, no party names, no opinions | world |
| 18 | richest-bollywood-actors | bollywood-stars | Top 10: Richest Bollywood actors (est. net worth ₹ crore) | bollywood |
| 19 | most-followed-women-instagram | social-media | Top 10: Most-followed women on Instagram worldwide (crore followers). Flags | tech |
| 20 | best-selling-games | gaming | Top 10: Best-selling video games of all time (crore copies). Glyph initials | tech |
| 21 | india-states-population-2026 | india-states | Most populous Indian states (crore people, latest estimate) | geo |
| 22 | richest-countries-gdp-2026 | world-vs-india | Biggest economies by GDP (where India stands) | world |
| 23 | bollywood-highest-grossing | bollywood-box-office | Highest-grossing Hindi films of all time (titles only) | bollywood |
| 24 | price-2000-vs-2026 | money-then-vs-now | Price of things, 2000 vs 2026 (times costlier) | money |
| 25 | most-subscribed-indian-channels | youtube-internet | Most-subscribed Indian YouTube channels (names only, no logos) | tech |
| 26 | ipl-titles-by-team | cricket | IPL titles by team (team names in text, no logos) | cricket |
| 27 | tallest-statues-world | world-records | Tallest statues in the world (metres) | space |
| 28 | salary-by-profession-india | money-india | Average salary by profession in India (₹ per month) | money |
| 29 | india-longest-rivers | india-geo | Longest rivers flowing through India (km) | geo |
| 30 | t20i-most-sixes | cricket | Most sixes in T20 internationals | cricket |
| 31 | smartphone-users-by-year | youtube-internet | Indian smartphone users, 2010 to 2026 (crore) | tech |
| 32 | fastest-animals | science-fun | Fastest animals on earth (km/h) | geo |
| 33 | petrol-price-by-country | money-world | Petrol price per litre in rupees: India vs other countries | money |
| 34 | india-tallest-buildings | india-cities | Tallest buildings in India (metres) | city |
| 35 | test-most-wickets | cricket | Most Test wickets of all time | cricket |
| 36 | olympic-medals-india | sports | India's Olympic medal count by Games | sports |
| 37 | isro-vs-hollywood-budget | science-fun | ISRO mission budgets vs Hollywood film budgets (₹ crore) | space |
| 38 | india-states-literacy | india-states | Indian states by literacy rate (%) | geo |
| 39 | world-cup-wins-by-country | cricket | Cricket World Cup titles by country (ODI + T20) | cricket |
| 40 | most-populous-countries | world-vs-india | Most populous countries (crore people) | world |
| 41 | internet-speed-by-country | youtube-internet | Mobile internet speed: India vs the world (Mbps) | tech |
| 42 | longest-bridges-india | india-geo | Longest bridges in India (km) | geo |
| 43 | odi-most-runs-india | cricket | Most ODI runs by Indian batters | cricket |
| 44 | biggest-cities-india | india-cities | Biggest Indian cities by population (lakh) | city |
| 45 | cinema-ticket-then-now | money-then-vs-now | Average cinema ticket price by decade (₹) | money |
| 46 | highest-mountains-world | science-fun | Highest mountains in the world (metres) | geo |
| 47 | fastest-trains-world | world-vs-india | Fastest trains in the world vs Vande Bharat (km/h) | world |
| 48 | t20-world-cup-most-runs | cricket | Most runs in T20 World Cups | cricket |
| 49 | upi-transactions-by-year | money-india | UPI transactions per year, 2017 to 2026 (crore) | money |
| 50 | india-states-area | india-states | Largest Indian states by area (sq km) | geo |
| 51 | bollywood-most-expensive-films | bollywood-box-office | Most expensive Hindi films ever made (budget ₹ crore) | bollywood |
| 52 | ipl-most-runs | cricket | Most runs in IPL history | cricket |
| 53 | air-passengers-airports-india | india-cities | Busiest airports in India (passengers per year) | city |
