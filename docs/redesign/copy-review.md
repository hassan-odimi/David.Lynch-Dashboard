# Copy review: About and new page text

Register: case study, first person. Granularity: section level. Source: `about.py`.

## Section: A personal reflection

**Before**
I am fascinated by cinema that defies convention and invites deeper reflection. Only a few have done so like David Lynch. I have always admired his wonderfully strange personality, which reminds me of my grandfather's eccentric spirit. His work — with its surreal imagery and layered narratives — has profoundly influenced modern art and cinema.

This dashboard is my way of diving into the life of David Lynch through the books, art, and everyday objects that shaped his vision. I feel sadness at his passing, but his art and memory will live on through what he left behind.

**After**
I am fascinated by cinema that defies convention and invites deeper reflection. Few have done so like David Lynch. I have always admired his wonderfully strange personality, which reminds me of my grandfather's eccentric spirit. His work, with its surreal imagery and layered narratives, has [1] profoundly influenced modern art and cinema.

This site is my way of looking into David Lynch's life through the books, art and everyday objects [2] in his collection. I feel sadness at his passing, but his art and memory will live on through what he left behind.

**Summary**
T1 cut: 2 em dashes, "diving into"
T2: 2 calls surfaced as [1] and [2]
Gaps: 0

## Section: About the project

**Before**
This interactive dashboard showcases and analyses items from the David Lynch Collection, auctioned by Julien's Auctions. Features: Explore detailed auction data for scripts, props, memorabilia, and more. See price trends, top items, category breakdowns, and visual insights. Interactive charts, dynamic filters, and visual galleries.

**After**
This site analyses the 441 lots of the David Lynch Collection, auctioned by Julien's Auctions. It replaces a Streamlit dashboard I built earlier.

Multiples compare each sold price with the midpoint of the lot's estimate.
Sold prices are shown as they appear in the source. Whether they include buyer's premium is not known.
Categories were assigned from keywords in each lot title. They are my groupings, not the auction house's.
The Library covers 287 books in 38 lots. Of these, 167 have no named author: 159 are listed as unknown and 8 as various.

**Summary**
T1 cut: feature list, "showcases"
T3 restored: concrete specifics, method passive, one honest hedge on buyer's premium
Gaps: 0

## Section: Source

**Before**
All auction data was sourced from Julien's Auctions.

**After**
All auction data and lot images come from Julien's Auctions. The images are hosted on this site with credit to that source. This site is an independent study and is not affiliated with Julien's Auctions.

**Summary**
T3 restored: image source and independence statement, as the plan requires
Gaps: 1, the portrait of David Lynch has no photographer credit

## Section: Creator

**Before**
My name is Hassan Odimi, and I'm a UX Designer passionate about cinema, unconventional design, and creating meaningful interactive experiences. This project combines my love of film, data, and design — and I hope it invites reflection and curiosity.

You can explore more of my work at www.hassan-odimi.se

Feel free to reach out, connect, or collaborate — I'd love to hear from you.

**After**
My name is Hassan Odimi, and I am a UX designer with a passion for cinema, unconventional design and meaningful interactive experiences. This project combines my love of film, data and design, and I hope it invites reflection and curiosity.

You can see more of my work at hassan-odimi.se. Feel free to reach out, connect or collaborate.

**Summary**
T1 cut: 2 em dashes, emoji, "I'd love to hear from you"
Gaps: 0

## Your calls

| # | Used | Alternative | Why it's a call |
|---|------|-------------|-----------------|
| 1 | "in his collection" | "that shaped his vision" (original) | The data shows what was sold, not what shaped him |
| 2 | "has profoundly influenced" | "has influenced" | Your opinion, so the adverb can stay, but no source backs it |
| 3 | "It replaces a Streamlit dashboard I built earlier." | Cut the sentence | Honest project history, but readers may not need it |

Reply with the numbers you want flipped, e.g. `1, 3`.

## Gaps to fill

- Portrait of David Lynch on the About page: [NEEDS: photographer and permission]
