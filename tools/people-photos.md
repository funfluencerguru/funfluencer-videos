# Real photos of people for stats reels

Real people are NEVER AI-generated: only real, free-licence photos with credit.
Status: waiting for the owner. When photos arrive, Claude crops them into round badges as assets/icons/pp_<name>.png and adds the credit lines to tools/people-credits.csv; the daily task then uses them and puts "Photos: Wikimedia Commons (credits in comments/description)" plus the credits in the caption.

## Prompt for another AI tool (one that can browse the web)
Find ONE free-licence photo for each person in the list below, ONLY from Wikimedia Commons (commons.wikimedia.org).
Rules:
- Licence must be Public Domain, CC0, CC BY or CC BY-SA. Skip anything else (no Google Images, no news sites, no Instagram, no Getty).
- A clear head-and-shoulders photo, face looking at the camera, good light, no watermark, no other famous person in the frame, at least 600 px wide.
- Prefer recent photos (2018 or later).
- If no suitable free photo exists, write "NOT FOUND" for that person. Never use a look-alike, a drawing or an AI image.
Return a table with: name, Commons file page URL, direct image URL, author, licence. If you can, also give me the images as files named like virat_kohli.jpg.

## People list (likely items; the real top 10 is checked on the day)
Cricketers: Virat Kohli, Rohit Sharma, Sachin Tendulkar, MS Dhoni, Hardik Pandya, Jasprit Bumrah, Shubman Gill, Rishabh Pant, KL Rahul, Suryakumar Yadav, Ravindra Jadeja, Shreyas Iyer, Sourav Ganguly, Rahul Dravid, Yuvraj Singh, Anil Kumble, Chris Gayle, Martin Guptill, Muttiah Muralitharan, Shane Warne, James Anderson, Stuart Broad, Glenn McGrath, Nathan Lyon, Mahela Jayawardene, Babar Azam, Jos Buttler, David Warner, Mitchell Starc, Pat Cummins
Instagram (world): Cristiano Ronaldo, Lionel Messi, Selena Gomez, Kylie Jenner, Dwayne Johnson, Ariana Grande, Kim Kardashian, Beyonce, Khloe Kardashian, Justin Bieber, Taylor Swift, Kendall Jenner, Nicki Minaj, Jennifer Lopez, Neymar
Indian stars: Priyanka Chopra, Shraddha Kapoor, Alia Bhatt, Deepika Padukone, Katrina Kaif, Jacqueline Fernandez, Kiara Advani, Anushka Sharma, Nora Fatehi, Kriti Sanon, Disha Patani, Neha Kakkar, Shah Rukh Khan, Salman Khan, Akshay Kumar, Amitabh Bachchan, Hrithik Roshan, Aamir Khan, Juhi Chawla, Karan Johar
YouTubers: MrBeast (Jimmy Donaldson), Bhuvan Bam, CarryMinati (Ajey Nagar), Ashish Chanchlani, Techno Gamerz (Ujjwal Chaurasia), Sourav Joshi
Richest Indians: Mukesh Ambani, Gautam Adani, Shiv Nadar, Savitri Jindal, Dilip Shanghvi, Cyrus Poonawalla, Kumar Mangalam Birla, Radhakishan Damani, Lakshmi Mittal, Sunil Mittal
Prime Ministers of India: Jawaharlal Nehru, Indira Gandhi, Narendra Modi, Manmohan Singh, Atal Bihari Vajpayee, Rajiv Gandhi, P. V. Narasimha Rao, Morarji Desai

## Not in the list on purpose
- Kids' YouTube channels (children): never photos.
- Channel brands (T-Series, Cocomelon, SET India, Zee Music): logos are trademarks; initials stay.
- Wedding couples: private family members; the weddings reel keeps drawn icons.
