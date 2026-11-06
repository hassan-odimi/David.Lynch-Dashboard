import json,re,collections,statistics as st,sys
d=json.load(open("David Lynch Collection Data.json",encoding="utf-8"))
n=lambda x:int(re.sub(r'\D','',x))
rules=[
("Cameras & Film Gear",r"\b35mm print|\b(c-stands?|fog machine|megaphones?|hasselblad|moviola|vcr|blu-?rays?|laserdisc|dvds?|vhs|tv|capture and playback|walkie talkies)\b"),
("Clothing & Personal",r"\b(caps?|neckties|wingtips|socks|cuff links|jewelry|canes|hats?|ring|sunglasses|reading glasses|shirts?|jackets?|suits?|shoes|clothing|apparel)\b"),
("Lamps & Lighting",r"\b(jtl everlight|lighting|lamps?)\b"),
("Scripts & Papers",r"\b(scripts?|screenplays?|treatments?|storyboards?|notes|notebooks?|manuscripts?|presentations?|letters?|contracts?|call sheets?|sides)\b"),
("Books & Magazines",r"\b(books?|magazines?|volumes?|encyclop\w+|dictionar\w+|comics?|issues)\b"),
("Art & Prints",r"\b(paintings?|prints?|lithographs?|monoprints?|sculptures?|woodblock|drawings?|photographs?|photos?|posters?|artworks?|canvas|portrait|etchings?|serigraphs?|collage|art)\b"),
("Cameras & Film Gear",r"\b(cameras?|camcorders?|lens(es)?|tripods?|polaroids?|35mm|16mm|film|bolex|arri|light meters?|slate|monitors?|projectors?|clapper|dolly|editing)\b"),
("Music & Audio",r"\b(guitars?|bass|keyboards?|drums?|microphones?|mics?|speakers?|amps?|amplifiers?|mixers?|synth\w*|trumpet|cornet|saxophone|violin|piano|records?|vinyl|albums?|turntables?|stereo|audio|headphones?|pedals?|sampl\w+|recorders?|receivers?|cds?|harmonica|ukulele|banjo|mandolin|flute)\b"),
("Coffee & Kitchen",r"\b(mugs?|cups?|coffee|espresso|grinders?|bowls?|plates?|tableware|kitchen|cookware|knives|barware|kitchenware|pots?|pans?|teapots?|blender|toaster|refrigerator|microwave|la marzocco)\b"),
("Workshop & Tools",r"\b(saws?|sanders?|drills?|lathes?|routers?|planers?|jointers?|clamps?|tools?|workbench\w*|vacuum|compressors?|welders?|grinder|vises?|hammers?|wrench\w*|ladders?|sawhorses?|shapers?|nailers?|chisels?|paint|brushes|easels?)\b"),
("Lamps & Lighting",r"\b(lamps?|lights?|lighting|chandeliers?|sconces?)\b"),
("Furniture & Rugs",r"\b(sofas?|chairs?|tables?|desks?|stools?|benches|bench|cabinets?|shelves|shelving|dressers?|beds?|rugs?|carpets?|credenzas?|ottomans?|armchairs?|lounge|sideboards?|couch|bookcases?|nightstands?|mirrors?|screens?)\b"),
("Memorabilia",r"\b(memorabilia|props?|ephemera|scrapbook|awards?|trophy|trophies|twin peaks|mulholland|eraserhead|blue velvet|dune|wardrobe|jackets?|shirts?|suits?|hats?|shoes|ties?|clothing|costumes?|transcendental|meditation)\b"),
]
def cat(t):
    l=t.lower()
    for c,r in rules:
        if re.search(r,l): return c
    return "Household & Other"
R=[]
for k,i in enumerate(d):
    s=n(i["Sold Price"]); e=[n(x) for x in i["Estimated Price"].split('-')]
    lo,hi=e[0],e[-1]
    R.append(dict(k=k,id=i["Item ID"],t=i["Title"],s=s,lo=lo,hi=hi,x=round(s/((lo+hi)/2),1),c=cat(i["Title"]),u=i["Item URL"]))
json.dump(R,open(sys.argv[1]+"/items_raw.json","w"),ensure_ascii=False)
C=collections.defaultdict(list)
for r in R:C[r['c']].append(r)
for c,g in sorted(C.items(),key=lambda kv:-sum(r['s'] for r in kv[1])):
    print(c,len(g),sum(r['s'] for r in g),st.median(r['x'] for r in g))
print([r['t'] for r in C["Household & Other"]][:70])
import random;random.seed(3)
for c in C:
    if c!="Household & Other": print(c,[r['t'][:38] for r in random.sample(C[c],min(7,len(C[c])))])
