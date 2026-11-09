# Real-photo sheets for stats reels

Each sheet is one image made in another AI image tool. It holds a grid of photo tiles. Claude cuts the sheet into the round pillar badges with `tools/cut_photo_sheet.py` and saves them in assets/icons, so the daily runs can use them as `img:NAME` with no manual step.
If a sheet is missing, the run falls back to the drawn icons or flags.

## Status
- S1 india-landmarks: DONE 2026-11-09 -> assets/icons/ph_<state>.png (18 badges).
- S2 gold: DONE 2026-11-09 -> ph_gold_* (10 badges). Tiles 1 and 4 dropped: tile 1 showed the national emblem and the year as text, tile 4 came out as a cookie instead of a gold biscuit.
- S3 prices: DONE 2026-11-09 -> ph_milk, ph_chai, ph_samosa, ph_petrol, ph_lpg, ph_cinema_ticket, ph_bus, ph_bread, ph_rice, ph_onion, ph_auto, ph_gold_ring.
- S4 statues: DONE 2026-11-09 -> 10 ph_statue_* badges. Dropped tile 9 (did not look like the Statue of Equality, which is a seated figure) and tile 12 (Peter the Great statue stands on a sailing ship; this one did not).
- S5 professions: DONE 2026-11-09 -> 12 ph_job_* badges (invented people, not real persons).
- S6-S16: waiting. The first batch came as combined images (all sheets in one picture), where each photo is only about 80 px, too small and blurry for a badge. Each sheet must be its OWN full-size image.
- Named landmarks must really look like that landmark (S4 statues, S6 rivers, S9 buildings, S11 cities, S13 mountains, S14 trains, S15 airports, S16 bridges). In the first batch the mountains, trains, bridges and skylines all came out as look-alike generic pictures; a badge labelled "K2" must show K2. If a tool can't get them right, skip that sheet and the reel keeps drawn icons.
- Cut a sheet with: `[TOP=name,...] python3 tools/cut_photo_sheet.py <sheet> ph_name1,ph_name2,...` (TOP keeps the top of tall subjects such as statues inside the circle).

## How to use
1. Copy the COMMON PROMPT, then paste the tile list of ONE sheet under it.
2. Generate the image. Check that the tiles are in the right order and that there is no text or logos.
3. Send the image here with the sheet name (e.g. "sheet S5").

## COMMON PROMPT (paste first)
Create ONE square image, 2048 x 2048 px: a clean grid of 4 columns x 3 rows of equal square photo tiles, separated by 24 px pure white gaps, with a 24 px white border around the outside. Each tile is a realistic, high-quality photograph of ONE subject, centred and filling about 80% of the tile, natural light, sharp focus, softly blurred simple background, rich but natural colours. NO text, NO labels, NO numbers, NO watermarks, NO logos, NO brand names, NO recognisable people (only small generic figures where a tile asks for them). Keep every tile the same style. Tiles in this exact order, left to right, top to bottom:

## SHEETS (12 tiles each; spare tiles cover items that change in the research)

S1 india-landmarks (state population / literacy / area, 3 reels; use a 6 x 3 grid, 18 tiles: change "4 columns x 3 rows" to "6 columns x 3 rows")
1 Taj Mahal, Agra (Uttar Pradesh) 2 Gateway of India, Mumbai (Maharashtra) 3 Nalanda university ruins (Bihar) 4 Howrah Bridge at dusk (West Bengal) 5 Gwalior Fort (Madhya Pradesh) 6 Chennai Marina beach lighthouse (Tamil Nadu) 7 Hawa Mahal, Jaipur (Rajasthan) 8 Mysore Palace lit at night (Karnataka) 9 Statue of Unity (Gujarat) 10 Visakhapatnam RK Beach (Andhra Pradesh) 11 Chilika Lake with boats (Odisha) 12 Golconda Fort (Telangana) 13 Kerala backwater houseboat 14 Chitrakote Falls (Chhattisgarh) 15 India Gate, Delhi 16 Shimla Mall Road in snow (Himachal) 17 Goa beach with palms 18 Aizawl hills town (Mizoram)

S2 gold-1950-2026
1 small gold coin on a 1950s wooden table with a valve radio 2 gold bangle with a 1960s brass lamp 3 gold chain beside a 1970s rotary phone 4 gold biscuit beside a 1980s cassette player 5 gold coins beside a 1990s pager 6 gold bar beside a 2000s keypad phone 7 gold jewellery set beside a 2010s smartphone 8 shiny 10 g gold bar on a modern 2026 desk 9 stack of gold bars 10 Indian bridal gold jewellery set 11 gold coins pile 12 jeweller's weighing scale with gold

S3 price-then-vs-now (also reused for other money reels)
1 litre of milk in a steel can 2 cutting chai in a glass 3 two samosas on a plate 4 petrol pump nozzle 5 red LPG cylinder 6 cinema ticket stub 7 city bus 8 loaf of bread 9 1 kg rice in a sack 10 kg onions 11 auto-rickshaw 12 gold ring

S4 tallest-statues-world
1 Statue of Unity, India 2 Spring Temple Buddha, China 3 Laykyun Sekkya, Myanmar 4 Ushiku Daibutsu, Japan 5 Statue of Liberty, USA 6 The Motherland Calls, Russia 7 Christ the Redeemer, Brazil 8 Guanyin of Nanshan, China 9 Statue of Equality, Hyderabad 10 Great Buddha of Thailand 11 African Renaissance Monument, Senegal 12 Peter the Great statue, Moscow
(note: some statues are religious figures; they appear only as landmarks with their height)

S5 salary-by-profession (generic workers, faces small or turned away)
1 software engineer at a laptop 2 doctor with stethoscope 3 school teacher at a blackboard 4 police officer 5 delivery rider on a scooter 6 chartered accountant with ledgers 7 airline pilot in a cockpit 8 nurse 9 construction worker 10 bank clerk 11 farmer in a field 12 chef in a kitchen

S6 india-longest-rivers
1 Ganga at Varanasi ghats at sunrise 2 Godavari river bridge 3 Krishna river 4 Yamuna 5 Narmada marble rocks 6 Brahmaputra 7 Indus in Ladakh 8 Mahanadi 9 Kaveri with Hogenakkal falls 10 Tapi 11 Sutlej 12 Chambal ravines

S7 smartphone-users-by-year
1 basic keypad phone (2010) 2 early touchscreen phone 3 phone with 3G icon on screen 4 budget Android phone 5 phone showing a video call 6 phone with UPI-style QR scan screen (no logos) 7 hand holding a 5G phone 8 family sharing one phone 9 village shop with phone 10 student with phone 11 crowd of phones at a concert 12 phone on a charging stand

S8 fastest-animals
1 peregrine falcon diving 2 cheetah running 3 golden eagle 4 sailfish leaping 5 pronghorn 6 blackbuck (India) 7 lion running 8 horse galloping 9 greyhound 10 ostrich running 11 kangaroo jumping 12 hare running

S9 india-tallest-buildings and S11 cities: night skylines
S9: 1 Mumbai Worli tall residential tower at night 2 Mumbai Lodha-style twin towers 3 Mumbai skyscraper cluster 4 Kolkata tall tower 5 Noida high-rise 6 Gurugram glass towers 7 Bengaluru tech park towers 8 Hyderabad high-rise 9 Chennai skyline 10 Ahmedabad GIFT City towers 11 Pune skyline 12 Mumbai Marine Drive at night
(no brand names or signs on buildings)

S10 isro-missions
1 PSLV rocket lifting off 2 GSLV rocket on the launch pad 3 lunar lander on the Moon 4 Moon rover with tracks 5 orbiter above Mars 6 sun-observing spacecraft 7 satellite with solar panels 8 mission control room (no faces) 9 Sriharikota launch pad at night 10 astronaut capsule splashdown 11 Earth from orbit 12 rocket stages separating

S11 biggest-cities-india
1 Mumbai Bandra-Worli Sea Link 2 Delhi Connaught Place 3 Bengaluru Vidhana Soudha 4 Hyderabad Charminar street 5 Ahmedabad Sabarmati riverfront 6 Chennai Kapaleeshwarar street (or Central station) 7 Kolkata yellow taxis on Howrah Bridge 8 Surat diamond market street 9 Pune Shaniwar Wada 10 Jaipur pink city street 11 Lucknow Rumi Darwaza 12 Kanpur Ganga barrage

S12 cinema-ticket-then-now
1 1970s single-screen cinema hall 2 1980s hand-painted film hoarding (no real faces, no titles) 3 1990s ticket window queue 4 2000s cinema with balcony seats 5 multiplex lobby 6 recliner seats in a modern hall 7 popcorn tub 8 3D glasses 9 paper ticket stub 10 phone showing a ticket QR 11 projector beam 12 big screen with audience from behind

S13 highest-mountains-world
1 Mount Everest 2 K2 3 Kangchenjunga 4 Lhotse 5 Makalu 6 Cho Oyu 7 Dhaulagiri 8 Manaslu 9 Nanga Parbat 10 Annapurna 11 Nanda Devi 12 Kamet

S14 fastest-trains-world
1 Shanghai maglev train 2 Chinese Fuxing high-speed train 3 Japanese Shinkansen bullet train 4 French TGV 5 German ICE 6 Italian Frecciarossa 7 Spanish AVE 8 Korean KTX 9 Indian Vande Bharat Express 10 Indian Rajdhani Express 11 Gatimaan Express 12 Mumbai-Ahmedabad bullet train construction

S15 busiest-airports-india
1 Delhi airport terminal 2 Mumbai airport terminal with peacock-style roof 3 Bengaluru garden terminal 4 Hyderabad airport 5 Chennai airport 6 Kolkata airport 7 Ahmedabad airport 8 Kochi solar airport 9 Pune airport 10 Goa airport 11 plane taking off at sunset 12 airport crowd from behind
(no airline logos)

S16 longest-bridges-india
1 Mumbai Trans Harbour Link (Atal Setu) 2 Bhupen Hazarika (Dhola-Sadiya) bridge 3 Mahatma Gandhi Setu, Patna 4 Bandra-Worli Sea Link 5 Bogibeel bridge 6 Vembanad rail bridge, Kochi 7 Vikramshila Setu 8 Chenab rail bridge 9 Pamban bridge 10 Howrah Bridge 11 Dibang River bridge 12 Signature Bridge, Delhi

## Real people (NOT made with AI)
21 reels feature real people. Claude does not make or use AI-generated look-alikes of real people. They can show wrong faces with real names, and can break platform rules on synthetic media. For these, send real photos you have the right to use (your own, or free-licence photos such as Wikimedia Commons, with credit in the caption). One photo per person is enough; Claude crops them into circles. Without photos these reels use flags and initials.
- Fastest to 1M subs; Top 10 YouTube world; fastest to 100M; Indian YouTube channels; Indian gaming channels (creators)
- Top 10 Instagram world; women on Instagram; Indians on Instagram; Indian actresses; cricketers on Instagram
- Richest IPL players; jersey numbers; T20I sixes; Test wickets; ODI runs (India); T20 World Cup runs; IPL most runs
- Richest Indians; richest Bollywood actors; most expensive weddings; longest-serving PMs

## No picture needed (flags, initials or titles stay)
Countries topics (independence, GDP, population, petrol price, internet speed, Olympic medals, World Cup titles) keep flags. IPL titles by team (team logos are trademarks), films (posters are copyrighted), video games (game art is copyrighted) and UPI keep drawn badges and titles.
